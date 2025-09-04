<?php

namespace App\Http\Repositories;

use App\Exports\InvoicesExport;
use App\Http\Interfaces\InvoiceRepositoryInterface;
use App\Models\File;
use App\Models\Invoice;
use App\Models\InvoiceItem;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;
use Maatwebsite\Excel\Facades\Excel;

class InvoiceRepository extends BaseRepository implements InvoiceRepositoryInterface
{
    public function __construct(Invoice $model)
    {
        parent::__construct($model);
    }


    public function upload($data, $request)
    {
        $results = [];

        // Define helper functions once
        if (!function_exists('normalize_arabic_digits')) {
            function normalize_arabic_digits(?string $s): ?string
            {
                if ($s === null)
                    return null;
                $map = [
                    '٠' => '0',
                    '١' => '1',
                    '٢' => '2',
                    '٣' => '3',
                    '٤' => '4',
                    '٥' => '5',
                    '٦' => '6',
                    '٧' => '7',
                    '٨' => '8',
                    '٩' => '9',
                    '۰' => '0',
                    '۱' => '1',
                    '۲' => '2',
                    '۳' => '3',
                    '۴' => '4',
                    '۵' => '5',
                    '۶' => '6',
                    '۷' => '7',
                    '۸' => '8',
                    '۹' => '9',
                ];
                return strtr($s, $map);
            }
        }

        if (!function_exists('to_int_or_null')) {
            function to_int_or_null(?string $s): ?int
            {
                if ($s === null)
                    return null;
                $s = normalize_arabic_digits($s);
                $digits = preg_replace('/\D+/', '', $s);
                return $digits !== '' ? (int) $digits : null;
            }
        }

        // Process each file
        foreach ($data['files'] as $file) {
            try {
                if (!$file instanceof \Illuminate\Http\UploadedFile) {
                    $results[] = [
                        'error' => 'Invalid file object',
                        'data' => $file
                    ];
                    continue;
                }

                $storedPath = $file->store('invoices', 'public');
                $absPath = Storage::disk('public')->path($storedPath);
                $type = strtolower($file->getClientOriginalExtension()) === 'pdf' ? 'pdf' : 'img';

                $result = DB::transaction(function () use ($type, $storedPath, $absPath, $file) {
                    // Create file record
                    $fileRecord = File::create([
                        'type' => $type,
                        'path' => $storedPath,
                        'title' => $file->getClientOriginalName(),
                    ]);

                    // Call Python service with the file
                    $url = config('services.ocr.endpoint');
                    \Log::info("Processing file: " . $file->getClientOriginalName());

                    $resp = Http::timeout(60)
                        ->attach('file', file_get_contents($absPath), $file->getClientOriginalName())
                        ->post($url . '/analyze', [
                            'filename' => $file->getClientOriginalName(),
                        ]);

                    if ($resp->failed()) {
                        throw new \RuntimeException('Python service error: ' . $resp->status() . ' ' . $resp->body());
                    }

                    $responseData = $resp->json();
                    $regions = collect($responseData['finale_words'] ?? []);
                    $byRegion = $regions->mapWithKeys(function ($item) {
                        $region = isset($item['region']) ? trim((string) $item['region']) : '';
                        $words = isset($item['words']) ? trim((string) $item['words']) : '';
                        return [$region => $words];
                    });

                    // Convenience getter
                    $get = function ($arabicLabel) use ($byRegion) {
                        return $byRegion[$arabicLabel] ?? null;
                    };

                    $mapped = [
                        'name' => $get('السادة') ?: 'Invoice',
                        'invoice_number' => to_int_or_null($get('رقم')) ?: 0,
                        'client_name' => $get('السادة') ?: "لا يوجد",
                        'doctor_name' => $get('الطبيب') ?: "لا يوجد",
                        'patient_name' => $get('المريض') ?: "لا يوجد",
                        'total_price' => to_int_or_null($get('الاجمالي') ?? $get('القيمة')) ?: 0,
                        'date' => normalize_arabic_digits($get('تاريخ')) ?: "0/0/0",
                        'notes' => trim(implode(' | ', array_filter([
                            $get('المواصفات'),
                            $get('الافرادي'),
                            $get('الكمية'),
                            $get('القيمة'),
                        ]))),
                    ];



                    $payload = validator($mapped, [
                        'name' => 'required|string|max:255',
                        'invoice_number' => 'required|integer',
                        'client_name' => 'nullable|string|max:255',
                        'doctor_name' => 'nullable|string|max:255',
                        'patient_name' => 'nullable|string|max:255',
                        'total_price' => 'nullable|integer',
                        'date' => 'nullable|string|max:255',
                        'notes' => 'nullable|string',
                    ])->validate();

                    $invoice = Invoice::create($payload + [
                        'file_id' => $fileRecord->id,
                        'user_id' => Auth::id(),
                    ]);

                    $quantity = (int) $get('الكمية');
                    $price = (int) $get('الافرادي');
                    $item = InvoiceItem::create([
                        'invoice_id' => $invoice->id,
                        'description' => $get('المواصفات'),
                        'quantity' => $quantity,
                        'price' => $price,
                        'value' => $price * $quantity,
                    ]);

                    return $invoice;
                });

                // Add successful result to results array
                $results[] = $result;

            } catch (\Throwable $e) {
                // Delete the stored file if there was an error
                if (isset($storedPath)) {
                    Storage::disk('public')->delete($storedPath);
                }

                // Add error to results array
                $results[] = [
                    'error' => $e->getMessage(),
                    'filename' => $file->getClientOriginalName(),
                ];
            }
        }

        return $results;
    }

    public function exportSelected($data)
    {
        $base = $data['filename'] ?? ('invoices_' . now()->format('Ymd_His'));
        $relPath = "exports/{$base}.xlsx";
        $disk = 'public';

        Excel::store(new InvoicesExport($data['ids'], Auth::user()?->id), $relPath, $disk);

        $file = File::create([
            'type' => 'xlsx',
            'path' => $relPath,
            'title' => $base,
        ]);

        return [
            'file_id' => $file->id,
            'public_url' => Storage::disk($disk)->url($relPath)
        ];
    }


    public function update($id, $data)
    {
        if (isset($data["items"])) {
            foreach ($data['items'] as $item) {
                $it = InvoiceItem::find($item['id']);
                $it->updated([
                    'description' => $item['description'] ?? "",
                    'quantity' => $item['quantity'] ?? 1
                ]);
            }
        }
        $invoice = Invoice::find($id);
        $invoice->updated([
            "invoice_number" => $data['invoice_number'],
            "client_name" => $data['client_name'],
            "doctor_name" => $data['doctor_name'],
            "patient_name" => $data['patient_name'],
            "total_price" => $data['total_price'],
            "date" => $data['date']
        ]);
        return $invoice;
    }
}
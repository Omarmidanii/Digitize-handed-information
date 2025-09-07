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

    private function toWesternDigits(string $s): string
    {
        $e = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
        $w = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
        return str_replace($e, $w, $s);
    }


    private function parseMoney(string|int|float|null $raw): string
    {
        if ($raw === null)
            return '0';
        $s = $this->toWesternDigits((string) $raw);
        // remove currency labels and any non-digit separators except dot/comma
        $s = preg_replace('/[^\d.,]/u', '', $s) ?? '0';
        // if both , and . exist, assume , is thousands; else strip thousands commas
        if (strpos($s, ',') !== false && strpos($s, '.') !== false) {
            $s = str_replace(',', '', $s);       // 1,234,567.89 -> 1234567.89
        } else {
            $s = str_replace(',', '', $s);       // 1,234,567 -> 1234567
        }
        // safe default: keep as decimal string
        if ($s === '' || $s === '.')
            $s = '0';
        return $s;
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
        // Add once near your helpers
        if (!function_exists('normalize_arabic_label')) {
            function normalize_arabic_label(?string $s): ?string
            {
                if ($s === null)
                    return null;
                // unify alef/ta marbuta/hamza/tatweel
                $s = strtr($s, [
                    'أ' => 'ا',
                    'إ' => 'ا',
                    'آ' => 'ا',
                    'ٱ' => 'ا',
                    'ة' => 'ه',
                    'ى' => 'ي',
                    'ؤ' => 'و',
                    'ئ' => 'ي',
                    'ـ' => ''
                ]);
                return trim($s);
            }
        }

        if (!function_exists('to_float_or_null')) {
            function to_float_or_null(?string $s): ?float
            {
                if ($s === null)
                    return null;
                $s = normalize_arabic_digits($s);
                // Strip currency and spaces, keep digits , .
                $s = trim(preg_replace('/[^\d,.\-]/u', '', $s) ?? '');
                if ($s === '')
                    return null;

                // If both , and . exist, treat , as thousands sep
                if (strpos($s, ',') !== false && strpos($s, '.') !== false) {
                    $s = str_replace(',', '', $s);
                } else {
                    // only one separator → make it a dot
                    $s = str_replace(',', '.', $s);
                }
                return is_numeric($s) ? (float) $s : null;
            }
        }

        // Process each file
        foreach ($data['files'] as $file) {
        // $testPath = storage_path('app/Invoices/CCI_000888.jpg'); // put your test file here
        // $file = new UploadedFile(
        //     $testPath,
        //     basename($testPath),
        //     mime_content_type($testPath),
        //     null,
        //     true // mark as "test mode" so Laravel won’t check if file was uploaded via HTTP
        // );

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
                $url = config('services.ocr.endpoint');
                $total = Cache::get('metrics:requests_total', 0);
                if($total%2 == 0){
                    $url = config('services.ocr.endpoint') . '/analyze';
                }else{
                    $url = config('services.ocr.endpoint') . '/analyze/hand';
                }
                // Call Python service with the file
                set_time_limit(300);
                $resp = Http::timeout(240)
                    ->connectTimeout(10)
                    ->attach('file', file_get_contents($absPath), $file->getClientOriginalName())
                    ->post($url , [
                        'filename' => $file->getClientOriginalName(),
                    ]);

                if ($resp->failed()) {
                    throw new \RuntimeException('Python service error: ' . $resp->status() . ' ' . $resp->body());
                }
                $responseData = $resp->json();
                $body = $responseData['finale_words'] ?? $responseData;

                $regions = collect($body['data'] ?? []);
                $byRegion = $regions->mapWithKeys(function ($item) {
                    $region = isset($item['region']) ? trim((string) $item['region']) : '';
                    $words = isset($item['words']) ? trim((string) $item['words']) : '';
                    return [$region => $words];
                });
                \Log::info($byRegion);
                // Convenience getter
                $get = function ($arabicLabel) use ($byRegion) {
                    return $byRegion[$arabicLabel] ?? null;
                };

                $itemsRows = collect($body['items'] ?? []);

                $parsedItems = $itemsRows->map(function (array $row) {
                    $desc = trim((string) ($row['المواصفات'] ?? ''));
                    $qty = to_float_or_null($row['الكمية'] ?? null) ?? 1;
                    $unit = to_float_or_null($row['الافرادي'] ?? null) ?? 0;
                    $val = to_float_or_null($row['القيمة'] ?? null);
                    if ($val === null)
                        $val = $qty * $unit;

                    return [
                        'description' => $desc,
                        'quantity' => $qty,
                        'price' => $unit,
                        'value' => $val,
                    ];
                })->filter(fn($i) => $i['description'] !== '' || $i['quantity'] || $i['price'] || $i['value'])
                    ->values();

                // Build notes from items (optional)
                $itemsNote = $parsedItems->map(
                    fn($i) =>
                    trim(sprintf(
                        '%s × %s @ %s = %s',
                        $i['description'] ?: 'بدون وصف',
                        rtrim(rtrim(number_format((float) $i['quantity'], 2, '.', ''), '0'), '.'),
                        rtrim(rtrim(number_format((float) $i['price'], 2, '.', ''), '0'), '.'),
                        rtrim(rtrim(number_format((float) $i['value'], 2, '.', ''), '0'), '.')
                    ))
                )->implode(' | ');

                $mapped = [
                    'name' => $get('السادة') ?: 'Invoice',
                    'invoice_number' => to_int_or_null($get('رقم')) ?: 0,
                    'client_name' => $get('السادة') ?: "لا يوجد",
                    'doctor_name' => $get('الطبيب') ?: "لا يوجد",
                    'patient_name' => $get('المريض') ?: "لا يوجد",
                    'total_price' => to_int_or_null($get('الاجمالي') ?? $get('القيمة')) ?: 0,
                    'date' => normalize_arabic_digits($get('تاريخ')) ?: "0/0/0",
                    'notes' => $itemsNote,
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

                foreach ($parsedItems as $it) {
                    $quantity = (float) $it['quantity'];




                    $price = $this->parseMoney($it['الافرادي'] ?? $it['السعر'] ?? '');
                    $value = $this->parseMoney($it['القيمة'] ?? '');
                    $qty = (int) preg_replace('/\D+/', '', (string) ($item['الكمية'] ?? '1')) ?: 1;

                    InvoiceItem::create([
                        'invoice_id' => $invoice->id,
                        'description' => $it['description'],
                        'quantity' => $quantity,
                        'price' => $price,
                        'value' => $value,
                    ]);
                }

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
        // }

        return $results;
    }

    public function exportSelected($data)
    {
        // $base = $data['filename'] ?? ('invoices_' . now()->format('Ymd_His'));
        $base = random_int(0, 200) . "report";
        $relPath = "report.pdf";
        $disk = 'public';

        // Excel::store(new InvoicesExport($data['ids'], Auth::user()?->id), $relPath, $disk);

        File::create([
            'type' => 'pdf',
            'path' => $relPath,
            'title' => $base,
        ]);

        return [
            "done"
        ];
    }


    public function update($id, $data)
    {
        if (isset($data["items"])) {
            foreach ($data['items'] as $item) {
                $it = InvoiceItem::find($item['id']);
                $it->update([
                    'description' => $item['description'] ?? "",
                    'quantity' => $item['quantity'] ?? 1
                ]);
            }
        }
        $invoice = Invoice::find($id);
        $invoice->update([
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
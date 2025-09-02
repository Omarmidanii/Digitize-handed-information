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
        $user = Auth::user();
        $uploaded = $request->file('file');
        // $testPath = storage_path('app/Invoices/Test.jpg'); // put your test file here
        // $uploaded = new UploadedFile(
        //     $testPath,
        //     basename($testPath),
        //     mime_content_type($testPath),
        //     null,
        //     true // mark as "test mode" so Laravel won’t check if file was uploaded via HTTP
        // );
        $storedPath = $uploaded->store('invoices', 'public');
        $absPath = Storage::disk('public')->path($storedPath);

        $type = strtolower($uploaded->getClientOriginalExtension()) === 'pdf' ? 'pdf' : 'img';

        try {
            return DB::transaction(function () use ($data, $user, $type, $storedPath, $absPath, $uploaded) {
                $file = File::create([
                    'type' => $type,
                    'path' => $storedPath,
                    'title' => $validated['title'] ?? null,
                ]);
                // call Python service with the file
                $url = config('services.ocr.endpoint');
                \Log::info("here we go");
                $resp = Http::timeout(60)
                    ->attach('file', file_get_contents($absPath), $uploaded->getClientOriginalName())
                    ->post($url . '/analyze', [
                        'filename' => $uploaded->getClientOriginalName(),
                    ]);


                if ($resp->failed()) {
                    throw new \RuntimeException('Python service error: ' . $resp->status() . ' ' . $resp->body());
                }

                $data = $resp->json();
                if (!function_exists('normalize_arabic_digits')) {
                    function normalize_arabic_digits(?string $s): ?string
                    {
                        if ($s === null)
                            return null;
                        // Arabic-Indic and Eastern Arabic-Indic → Western
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
                        // keep only digits
                        $digits = preg_replace('/\D+/', '', $s);
                        return $digits !== '' ? (int) $digits : null;
                    }
                }
                $regions = collect($data['finale_words'] ?? []);
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
                    'file_id' => $file->id,
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

                return [
                    'file' => $file,
                    'invoice' => $invoice,
                    'item' => $item
                ];
            });
        } catch (\Throwable $e) {

            if (isset($storedPath)) {
                Storage::disk('public')->delete($storedPath);
            }
            throw $e;
        }
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
}
<?php
// app/Exports/InvoicesExport.php
namespace App\Exports;

use App\Models\Invoice;
use Illuminate\Database\Eloquent\Builder;
use Maatwebsite\Excel\Concerns\FromQuery;
use Maatwebsite\Excel\Concerns\WithHeadings;
use Maatwebsite\Excel\Concerns\WithMapping;
use Maatwebsite\Excel\Concerns\WithColumnFormatting;
use Maatwebsite\Excel\Concerns\ShouldAutoSize;
use PhpOffice\PhpSpreadsheet\Style\NumberFormat;

class InvoicesExport implements FromQuery, WithHeadings, WithMapping, ShouldAutoSize, WithColumnFormatting
{
    public function __construct(
        protected array $ids,
        protected ?int $userId = null
    ) {
    }

    /** @return Builder */
    public function query()
    {
        $q = Invoice::query()->with('file')->whereIn('id', $this->ids);
        if ($this->userId) {
            $q->where('user_id', $this->userId);
        }
        return $q->orderBy('id');
    }

    public function headings(): array
    {
        return [
            'ID',
            'Name',
            'Invoice Number',
            'Client',
            'Doctor',
            'Patient',
            'Total Price',
            'Date',
            'Notes',
            'File Title',
            'File Type',
            'File Path'
        ];
    }

    public function map($invoice): array
    {
        return [
            $invoice->id,
            $invoice->name,
            $invoice->invoice_number,
            $invoice->client_name,
            $invoice->doctor_name,
            $invoice->patient_name,
            $invoice->total_price,
            $invoice->date,
            $invoice->notes,
            optional($invoice->file)->title,
            optional($invoice->file)->type,
            optional($invoice->file)->path,
        ];
    }

    public function columnFormats(): array
    {
        return [
            'C' => NumberFormat::FORMAT_NUMBER, // invoice_number
            'G' => NumberFormat::FORMAT_NUMBER, // total_price
        ];
    }
}
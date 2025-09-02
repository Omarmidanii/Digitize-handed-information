<?php

namespace App\Http\Resources\Invoice;

use App\Http\Resources\Items\ItemResource;
use App\Models\InvoiceItem;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class InvoiceResource extends JsonResource
{
    /**
     * Transform the resource into an array.
     *
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        $item = ItemResource::collection(InvoiceItem::where('invoice_id', $this->id)->get());
        return [
            'id' => $this->id,
            'photo' => $this->whenLoaded('file', function () {
                return $this->file->url;
            }),
            'item' => $item ?? null,
            'user' => $this->whenLoaded('user'),
            'invoice_number' => $this->invoice_number,
            'client_name' => $this->client_name,
            'doctor_name' => $this->doctor_name,
            'patient_name' => $this->patient_name,
            'total_price' => $this->total_price,
            'date' => $this->date,
            'notes' => $this->notes,
        ];
    }
}
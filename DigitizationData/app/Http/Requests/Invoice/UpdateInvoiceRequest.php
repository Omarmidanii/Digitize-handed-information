<?php

namespace App\Http\Requests\Invoice;

use Illuminate\Foundation\Http\FormRequest;

class UpdateInvoiceRequest extends FormRequest
{
    /**
     * Determine if the user is authorized to make this request.
     */
    public function authorize(): bool
    {
        return true;
    }

    /**
     * Get the validation rules that apply to the request.
     *
     * @return array<string, \Illuminate\Contracts\Validation\ValidationRule|array<mixed>|string>
     */
    public function rules(): array
    {
        return [
            'invoice_number' => "integer|sometimes",
            "client_name" => "string|sometimes|min:3",
            "doctor_name" => "string|sometimes|min:3",
            "patient_name" => "string|sometimes|min:3",
            "total_price" => "integer|sometimes|min:1",
            "date" => "string|sometimes",
            "items" => "array|sometimes",
            "items.*.description" => "string|sometimes",
            "items.*.quantity" => "integer|sometimes",
            "items.*.id" => "integer|exists:invoice_items,id"
        ];
    }
}
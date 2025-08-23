<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class InvoiceItem extends Model
{
    use HasFactory;
    protected $fillable = [
        'description',
        'value',
        'price',
        'category',
        'invoice_id',
        'quantity'
    ];

    protected $casts = [
        'quantity' => 'integer',
        'price' => 'integer',
        'value' => 'integer'
    ];
}
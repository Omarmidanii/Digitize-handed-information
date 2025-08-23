<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Invoice extends Model
{
    use HasFactory;
    protected $fillable = [
        'name',
        'invoice_number',
        'file_id',
        'user_id',
        'client_name',
        'doctor_name',
        'patient_name',
        'total_price',
        'date',
        'notes',
    ];

    protected $casts = [
        'invoice_number' => 'integer',
        'total_price' => 'integer',
    ];

    public function file()
    {
        return $this->belongsTo(File::class);
    }

    public function user()
    {
        return $this->belongsTo(User::class);
    }
}
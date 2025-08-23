<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class File extends Model
{
    use HasFactory;

    protected $fillable = [
        'type',
        'path',
        'title',
    ];

    /**
     * Relationships
     */
    public function invoices()
    {
        return $this->hasMany(Invoice::class);
    }

    public function getUrlAttribute()
    {
        return $this->path ? url($this->path) : null;
    }
}
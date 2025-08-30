<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;

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
        if (!$this->path)
            return null;
        $url = Storage::disk('public')->url($this->path);
        return Str::startsWith($url, ['http://', 'https://']) ? $url : asset($url);
    }
}
<?php

namespace App\Http\Repositories;

use App\Exports\InvoicesExport;
use App\Http\Interfaces\FileRepositoryInterface;
use App\Http\Interfaces\InvoiceRepositoryInterface;
use App\Http\Resources\GroupResource;
use App\Models\Classification;
use App\Models\File;
use App\Models\Invoice;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;
use Maatwebsite\Excel\Facades\Excel;

class FileRepository extends BaseRepository implements FileRepositoryInterface
{
    public function __construct(Invoice $model)
    {
        parent::__construct($model);
    }

    public function download($id)
    {

    }
}
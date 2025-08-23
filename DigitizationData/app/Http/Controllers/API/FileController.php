<?php

namespace App\Http\Controllers\API;

use App\Trait\ApiResponse;
use App\Http\Controllers\Controller;
use App\Http\Interfaces\InvoiceRepositoryInterface;
use App\Http\Resources\Invoice\InvoiceResourse;
use App\Models\File;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use Throwable;


class FileController extends Controller
{
    use ApiResponse;

    private $invoiceRepository;

    public function __construct(InvoiceRepositoryInterface $invoiceRepository)
    {
        $this->invoiceRepository = $invoiceRepository;
    }

    public function index()
    {
        try {
            $data = $this->invoiceRepository->index();
            return $this->SuccessMany($data, null, 'files indexed successfully');
        } catch (Throwable $th) {
            $code = 500;
            if ($th->getCode() != 0)
                $code = $th->getCode();
            return $this->Error(null, $th->getMessage(), $code);
        }
    }

    public function download(File $file)
    {
        $disk = 'public';
        abort_unless(Storage::disk($disk)->exists($file->path), 404);

        $ext = pathinfo($file->path, PATHINFO_EXTENSION);
        $name = ($file->title ?: pathinfo($file->path, PATHINFO_FILENAME));
        $name = Str::slug($name) . '.' . $ext;

        return Storage::disk($disk)->download($file->path, $name);
    }

    public function downloadFile($id)
    {
        $file = File::find($id);
        $ext = pathinfo($file->path, PATHINFO_EXTENSION);
        $name = ($file->title ?: pathinfo($file->path, PATHINFO_FILENAME));
        $name = Str::slug($name) . '.' . $ext;
        return Storage::disk('public')->download($file->path, $name);
    }


}
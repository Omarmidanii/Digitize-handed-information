<?php

namespace App\Http\Controllers\API;

use App\Http\Requests\Invoice\UpdateInvoiceRequest;
use App\Http\Resources\Invoice\InvoiceResource;
use App\Trait\ApiResponse;
use App\Http\Controllers\Controller;
use App\Http\Interfaces\InvoiceRepositoryInterface;
use App\Http\Requests\Invoice\StoreInvoiceRequest;
use App\Models\File;
use Illuminate\Support\Str;
use Throwable;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;

class InvoiceController extends Controller
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
            $data = $this->invoiceRepository->index(['file']);
            return $this->SuccessMany($data, InvoiceResource::class, 'Invoices indexed successfully');
        } catch (Throwable $th) {
            $code = 500;
            if ($th->getCode() != 0)
                $code = $th->getCode();
            return $this->Error(null, $th->getMessage(), $code);
        }
    }

    public function upload(StoreInvoiceRequest $request)
    {
        try {
            $validated = $request->validated();
            $data = $this->invoiceRepository->upload($validated, $request);
            return $this->SuccessOne($data, null, 'Invoice created successfully');
        } catch (Throwable $th) {
            $code = 500;
            if ($th->getCode() != 0)
                $code = $th->getCode();
            return $this->Error(null, $th->getMessage(), $code);
        }
    }

    public function show($id)
    {
        try {
            $data = $this->invoiceRepository->show($id, ['file']);
            return $this->SuccessOne($data, InvoiceResource::class, 'Successful');
        } catch (Throwable $th) {
            $code = 500;
            if ($th->getCode() != 0)
                $code = $th->getCode();
            return $this->Error(null, $th->getMessage(), $code);
        }
    }


    public function update(UpdateInvoiceRequest $request, $id)
    {
        try {
            $validated = $request->validated();
            $data = $this->invoiceRepository->update($id, $validated);
            return $this->SuccessOne($data, InvoiceResource::class, 'Invoice updated successfully');
        } catch (Throwable $th) {
            $code = 500;
            if ($th->getCode() != 0)
                $code = $th->getCode();
            return $this->Error(null, $th->getMessage(), $code);
        }
    }

    public function exportSelected(Request $request)
    {
        try {
            $validated = $request->validate([
                'start_date' => 'string',
                'end_date' => 'string',
            ]);
            $data = $this->invoiceRepository->exportSelected($validated);
            $file = File::find(57);
            $ext = pathinfo($file->path, PATHINFO_EXTENSION);
            $name = ($file->title ?: pathinfo($file->path, PATHINFO_FILENAME));
            $name = Str::slug($name) . '.' . $ext;
            return Storage::disk("public")->download($file->path, $name);
        } catch (Throwable $th) {
            $code = 500;
            if ($th->getCode() != 0)
                $code = $th->getCode();
            return $this->Error(null, $th->getMessage(), $code);
        }

    }


    public function destroy($id)
    {
        try {
            $this->invoiceRepository->destroy($id);
            return $this->SuccessOne(null, null, 'Invoice deleted successfully');
        } catch (Throwable $th) {
            return $this->Error(null, $th->getMessage(), 404);
        }
    }


}
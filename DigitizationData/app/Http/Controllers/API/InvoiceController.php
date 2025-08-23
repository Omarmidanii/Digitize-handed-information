<?php

namespace App\Http\Controllers\API;

use App\Trait\ApiResponse;
use App\Http\Controllers\Controller;
use App\Http\Interfaces\InvoiceRepositoryInterface;
use App\Http\Requests\Invoice\StoreInvoiceRequest;
use App\Http\Resources\Invoice\InvoiceResourse;
use Throwable;
use Illuminate\Http\Request;


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
            $data = $this->invoiceRepository->index();
            return $this->SuccessMany($data, InvoiceResourse::class, 'Invoices indexed successfully');
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
            return $this->SuccessOne($data['invoice'], InvoiceResourse::class, 'Invoice created successfully');
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
            $data = $this->invoiceRepository->show($id);
            return $this->SuccessOne($data, InvoiceResourse::class, 'Successful');
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
            $validated = $request->$request->validated([
                'ids' => 'required|array|min:1',
                'ids.*' => 'integer|distinct|exists:invoices,id',
                'filename' => 'sometimes|string|max:100',
            ]);
            $data = $this->invoiceRepository->exportSelected($validated);
            return $this->SuccessOne($data, InvoiceResourse::class, 'Invoices exported successfully');
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
<?php

namespace App\Http\Interfaces;

interface InvoiceRepositoryInterface extends BaseRepositoryInterface
{

    public function upload($data, $request);

    public function exportSelected($data);
}
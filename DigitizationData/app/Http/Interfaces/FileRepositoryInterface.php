<?php

namespace App\Http\Interfaces;

interface FileRepositoryInterface extends BaseRepositoryInterface
{
    public function download($id);
}
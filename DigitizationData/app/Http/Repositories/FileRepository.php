<?php

namespace App\Http\Repositories;

use App\Http\Interfaces\FileRepositoryInterface;
use App\Models\File;

class FileRepository extends BaseRepository implements FileRepositoryInterface
{
    public function __construct(File $model)
    {
        parent::__construct($model);
    }

    public function download($id)
    {

    }
}
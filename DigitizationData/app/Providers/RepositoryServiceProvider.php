<?php

namespace App\Providers;

use App\Http\Interfaces\BaseRepositoryInterface;
use App\Http\Interfaces\FileRepositoryInterface;
use App\Http\Interfaces\InvoiceRepositoryInterface;
use App\Http\Interfaces\UserRepositoryInterface;
use App\Http\Repositories\BaseRepository;
use App\Http\Repositories\FileRepository;
use App\Http\Repositories\InvoiceRepository;

use App\Http\Repositories\UserRepository;
use Illuminate\Support\ServiceProvider;

class RepositoryServiceProvider extends ServiceProvider
{
    /**
     * Register services.
     */
    public function register(): void
    {
        $this->app->bind(BaseRepositoryInterface::class, BaseRepository::class);
        $this->app->bind(UserRepositoryInterface::class, UserRepository::class);
        $this->app->bind(InvoiceRepositoryInterface::class, InvoiceRepository::class);
        $this->app->bind(FileRepositoryInterface::class, FileRepository::class);
    }

    /**
     * Bootstrap services.
     */
    public function boot(): void
    {
        //
    }
}
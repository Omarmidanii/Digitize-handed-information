<?php

use App\Http\Controllers\API\FileController;
use App\Http\Controllers\API\InvoiceController;
use App\Http\Controllers\Auth\AuthController;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

Route::get('/user', function (Request $request) {
    return $request->user();
})->middleware('auth:sanctum');

Route::controller(AuthController::class)->group(function () {
    Route::post('login', 'login');
    Route::post('logout', 'logout')->middleware('auth:sanctum');
    Route::get('ForgotPassword', 'ForgotPassword');
    Route::post('CheckCode', 'CheckCode');
    Route::post('ChangePassword', 'ChangePassword');
});

Route::middleware('auth:sanctum')->group(function () {
    Route::controller(InvoiceController::class)->prefix('invoices')->group(function () {
        Route::get('', 'index');
        Route::get('/{id}', 'show');
        Route::delete('/{id}', 'destroy');
        Route::get('/exportselected', ' ');
        Route::post('/upload', 'upload');
    });
    Route::controller(FileController::class)->prefix('files')->group(function () {
        Route::get('', 'index');
        Route::get('/download/{id}', 'downloadFile');
        Route::post('/download', 'download');
    });
});
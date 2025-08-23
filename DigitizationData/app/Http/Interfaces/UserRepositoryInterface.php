<?php

namespace App\Http\Interfaces;

use App\Http\Requests\Auth\ForgetPasswordRequest;

interface UserRepositoryInterface extends BaseRepositoryInterface
{
    public function ForgotPassword($email);
    public function CheckCode($ip, $email, $data);
    public function ChangePassword($ip, $id, $data);
}
<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Http\Interfaces\UserRepositoryInterface;
use App\Http\Requests\Auth\ChangePasswordRequest;
use App\Http\Requests\Auth\ForgetPasswordCodeRequest;
use App\Http\Requests\Auth\LoginRequest;
use App\Models\User;
use App\Trait\ApiResponse;
use Exception;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Validator;

class AuthController extends Controller
{
    use ApiResponse;
    private $userRepository;

    public function __construct(UserRepositoryInterface $userRepository)
    {
        $this->middleware('auth:sanctum', ['only' => 'logout']);
        $this->userRepository = $userRepository;
    }

    public function login(LoginRequest $request)
    {
        \Log::info("hello from here");
        try {
            $data = $request->validated();
            $user = User::where('email', $data['email'])->first();
            if (!is_null($user)) {
                if (!Auth::attempt(['email' => $data['email'], 'password' => $data['password']])) {
                    $message = 'User email & password do not match with our records.';
                    return response()->json(["message" => $message], 401);
                } else {
                    $user['access_token'] = $user->createToken("token")->plainTextToken;
                    return $this->SuccessOne($user, null, 'User Logged in Successfully');
                }
            } else {
                $message = 'User not found.';
                return response()->json(["message" => $message], 404);
            }
        } catch (Exception $e) {
            return $this->Error(null, $e, 500);
        }

    }

    public function ForgotPassword(Request $request)
    {
        try {
            $validator = Validator::make($request->all(), [
                'email' => 'required|string|email',
            ]);
            if ($validator->fails()) {
                return response()->json($validator->errors(), 422);
            }
            $email = $request->email;
            $data = $this->userRepository->ForgotPassword($email);
            return $this->SuccessOne($data, null, 'code sent successfully');
        } catch (\Throwable $th) {
            return $this->Error(null, $th->getMessage());
        }
    }

    public function CheckCode(ForgetPasswordCodeRequest $request)
    {
        try {
            $data = $request->validated();
            $ip = $request->ip();
            $res = $this->userRepository->CheckCode($ip, $data['email'], $data);
            if ($res == 1)
                return $this->SuccessOne($data, null, 'code is correct');
            else {
                $message = 'code not correct';
                return response()->json(["message" => $message], 401);
            }
        } catch (\Throwable $th) {
            return $this->Error(null, $th->getMessage());
        }
    }

    public function ChangePassword(ChangePasswordRequest $request)
    {

        try {
            $data = $request->validated();
            $ip = $request->ip();
            $res = $this->userRepository->ChangePassword($ip, $data['email'], $data);
            if ($res == 3)
                return $this->SuccessOne($data, null, 'password was changed successfully');
            else if ($res == 2) {
                $message = 'passwords do not match';
                return response()->json(["message" => $message], 401);
            } else {
                $message = 'an eror occurred try later';
                return response()->json(["message" => $message], 401);
            }
        } catch (\Throwable $th) {
            return $this->Error(null, $th->getMessage());
        }
    }

    public function logout()
    {
        Auth::user()->tokens()->delete();
        return $this->SuccessOne(null, null, 'Successfully logged out', 200);
    }
}
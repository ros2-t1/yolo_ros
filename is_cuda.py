import torch

print("CUDA available:", torch.cuda.is_available())
print("CUDA device count:", torch.cuda.device_count())

if torch.cuda.is_available():
    print("Current device index:", torch.cuda.current_device())
    print("Device name:", torch.cuda.get_device_name(torch.cuda.current_device()))
    print("Tensor on GPU:", torch.tensor([1.0, 2.0]).to('cuda'))
else:
    print("GPU를 사용할 수 없습니다. CPU를 사용합니다.")

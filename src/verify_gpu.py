import bpy

def verify_rtx3090():
    """验证 RTX 3090 和 OptiX 是否启用"""
    print("===== GPU 渲染配置验证 =====")
    
    # 检查渲染引擎
    if bpy.context.scene.render.engine != 'CYCLES':
        print("错误: 未使用 Cycles 渲染器")
        return False
    
    # 检查设备类型
    prefs = bpy.context.preferences
    cycles_prefs = prefs.addons['cycles'].preferences
    device_type = cycles_prefs.compute_device_type
    
    if device_type != 'OPTIX':
        print(f"警告: 未使用 OptiX 设备类型 (当前: {device_type})")
    
    # 检查设备
    enabled_devices = []
    for device in cycles_prefs.devices:
        if device.use:
            enabled_devices.append(device.name)
    
    if not enabled_devices:
        print("错误: 未启用任何 GPU 设备")
        return False
    
    print(f"已启用设备: {', '.join(enabled_devices)}")
    
    # 检查 OptiX 去噪
    if not bpy.context.scene.cycles.use_denoising:
        print("警告: 未启用去噪")
    elif bpy.context.scene.cycles.denoiser != 'OPTIX':
        print(f"警告: 未使用 OptiX 去噪 (当前: {bpy.context.scene.cycles.denoiser})")
    
    # 最终检查
    if bpy.context.scene.cycles.device == 'GPU':
        print("SUCCESS: GPU 渲染已正确配置")
        return True
    else:
        print("错误: 未使用 GPU 渲染")
        return False

if __name__ == "__main__":
    verify_rtx3090()
"""
设备管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from fastapi.responses import StreamingResponse
from io import BytesIO

from app.models import get_db
from app.models.models import Device
from app.schemas.schemas import Device as DeviceSchema, DeviceCreate, DeviceUpdate, DeviceWithDetails, BatchOperationResult, CommandExecutionRequest, BatchCommandExecutionRequest

# 创建路由器
router = APIRouter()

from app.services.netmiko_service import get_netmiko_service
from app.services.excel_service import import_devices_from_excel, generate_device_template


@router.get("/")
def get_devices(
    page: int = 1,
    page_size: int = 10,
    status: Optional[str] = None,
    vendor: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取设备列表
    """
    # 转换page和page_size为skip和limit
    skip = (page - 1) * page_size
    limit = page_size
    
    query = db.query(Device)
    
    if status:
        query = query.filter(Device.status == status)
    
    if vendor:
        query = query.filter(Device.vendor == vendor)
    
    # 获取总记录数
    total = query.count()
    # 获取分页数据
    devices = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "devices": devices,
        "page": page,
        "page_size": page_size
    }


@router.get("/all", response_model=Dict[str, Any])
async def get_all_devices(
    limit: int = Query(default=100, ge=1, le=5000, description="限制返回设备数量，默认100，最大5000"),
    offset: int = Query(default=0, ge=0, description="偏移量，用于分页"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    vendor: Optional[str] = Query(None, description="按厂商筛选"),
    db: Session = Depends(get_db)
):
    """
    获取所有设备列表，不受分页限制
    - 用于前端设备选择器等需要完整列表的场景
    - 默认最多返回100条记录，可通过limit参数调整，最大5000条
    """
    query = db.query(Device)

    if status:
        query = query.filter(Device.status == status)

    if vendor:
        query = query.filter(Device.vendor == vendor)

    total = query.count()
    devices = query.offset(offset).limit(limit).all()

    # 将SQLAlchemy对象转换为Pydantic模型
    device_schemas = [DeviceSchema.from_orm(device) for device in devices]

    return {
        "devices": device_schemas,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/template")
def download_device_template(db: Session = Depends(get_db)):
    """
    下载设备模板
    
    Args:
        db: SQLAlchemy会话
    
    Returns:
        Excel模板文件
    """
    try:
        # 生成模板
        template_stream = generate_device_template(db)
        
        # 返回流式响应，使用英文文件名避免编码问题
        return StreamingResponse(
            template_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=device_template.xlsx"
            }
        )
    except Exception as e:
        # 打印详细的错误信息和堆栈跟踪
        import traceback
        print(f"Error generating template: {str(e)}")
        print("Stack trace:")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成模板失败: {str(e)}"
        )


@router.get("/{device_id}", response_model=DeviceWithDetails)
def get_device(device_id: int, db: Session = Depends(get_db)):
    """
    获取设备详情
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    return device


@router.post("/", response_model=DeviceSchema, status_code=status.HTTP_201_CREATED)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """
    创建设备
    """
    # 检查IP地址是否已存在
    existing_device = db.query(Device).filter(Device.ip_address == device.ip_address).first()
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device with IP address {device.ip_address} already exists"
        )

    # 检查SN是否已存在
    if device.sn:
        existing_sn_device = db.query(Device).filter(Device.sn == device.sn).first()
        if existing_sn_device:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device with SN {device.sn} already exists"
            )

    # 创建设备
    db_device = Device(**device.model_dump())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@router.put("/{device_id}", response_model=DeviceSchema)
def update_device(device_id: int, device: DeviceUpdate, db: Session = Depends(get_db)):
    """
    更新设备
    """
    db_device = db.query(Device).filter(Device.id == device_id).first()
    if not db_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )

    # 更新设备信息
    update_data = device.model_dump(exclude_unset=True)

    # 检查IP地址是否已被其他设备使用
    if "ip_address" in update_data:
        existing_device = db.query(Device).filter(
            Device.ip_address == update_data["ip_address"],
            Device.id != device_id
        ).first()
        if existing_device:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"IP address {update_data['ip_address']} already used by another device"
            )

    # 检查SN是否已被其他设备使用
    if "sn" in update_data and update_data["sn"]:
        existing_sn_device = db.query(Device).filter(
            Device.sn == update_data["sn"],
            Device.id != device_id
        ).first()
        if existing_sn_device:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SN {update_data['sn']} already used by another device"
            )

    for field, value in update_data.items():
        setattr(db_device, field, value)

    db.commit()
    db.refresh(db_device)
    return db_device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: int, db: Session = Depends(get_db)):
    """
    删除设备
    """
    db_device = db.query(Device).filter(Device.id == device_id).first()
    if not db_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    
    db.delete(db_device)
    db.commit()
    return None


@router.post("/batch/delete", response_model=BatchOperationResult)
def batch_delete_devices(device_ids: List[int], db: Session = Depends(get_db)):
    """
    批量删除设备
    """
    success_count = 0
    failed_count = 0
    failed_devices = []
    
    for device_id in device_ids:
        try:
            db_device = db.query(Device).filter(Device.id == device_id).first()
            if db_device:
                db.delete(db_device)
                success_count += 1
            else:
                failed_count += 1
                failed_devices.append(f"Device {device_id} not found")
        except Exception as e:
            failed_count += 1
            failed_devices.append(f"Device {device_id}: {str(e)}")
    
    db.commit()
    
    return BatchOperationResult(
        success=failed_count == 0,
        message=f"Batch delete completed: {success_count} success, {failed_count} failed",
        total=len(device_ids),
        success_count=success_count,
        failed_count=failed_count,
        failed_devices=failed_devices if failed_devices else None
    )


@router.post("/batch/update-status", response_model=BatchOperationResult)
def batch_update_device_status(device_ids: List[int], status: str, db: Session = Depends(get_db)):
    """
    批量更新设备状态
    """
    success_count = 0
    failed_count = 0
    failed_devices = []
    
    for device_id in device_ids:
        try:
            db_device = db.query(Device).filter(Device.id == device_id).first()
            if db_device:
                db_device.status = status
                success_count += 1
            else:
                failed_count += 1
                failed_devices.append(f"Device {device_id} not found")
        except Exception as e:
            failed_count += 1
            failed_devices.append(f"Device {device_id}: {str(e)}")
    
    db.commit()
    
    return BatchOperationResult(
        success=failed_count == 0,
        message=f"Batch status update completed: {success_count} success, {failed_count} failed",
        total=len(device_ids),
        success_count=success_count,
        failed_count=failed_count,
        failed_devices=failed_devices if failed_devices else None
    )


@router.post("/{device_id}/test-connectivity")
async def test_connectivity(device_id: int, db: Session = Depends(get_db)):
    """
    测试设备连接性
    """
    # 获取设备信息
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    
    # 获取Netmiko服务
    netmiko_service = get_netmiko_service()
    
    # 连接测试
    connection = await netmiko_service.connect_to_device(device)
    
    # 更新设备状态
    if connection:
        # 连接成功，状态设置为活跃
        device.status = "active"
        result = {
            "success": True,
            "message": f"设备 {device.hostname} 连接成功",
            "status": "active"
        }
    else:
        # 连接失败，状态设置为离线
        device.status = "offline"
        result = {
            "success": False,
            "message": f"设备 {device.hostname} 连接失败",
            "status": "offline"
        }
    
    # 保存状态更新
    db.commit()
    db.refresh(device)
    
    return result


@router.post("/{device_id}/execute-command")
async def execute_command(device_id: int, command_request: CommandExecutionRequest, db: Session = Depends(get_db)):
    """
    执行设备命令
    
    Args:
        device_id: 设备ID
        command_request: 命令执行请求
        db: SQLAlchemy会话
    
    Returns:
        命令执行结果
    """
    from app.models.models import CommandHistory
    import time
    
    # 获取设备信息
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    
    # 获取命令和变量
    command = command_request.command
    variables = command_request.variables or {}
    template_id = command_request.template_id
    
    # 如果使用模板，获取模板并替换变量
    if template_id:
        from app.models.models import CommandTemplate
        template = db.query(CommandTemplate).filter(CommandTemplate.id == template_id).first()
        if template:
            # 简单的变量替换
            for var_name, var_value in variables.items():
                command = command.replace(f"{{{{{var_name}}}}}", str(var_value))
    
    # 获取Netmiko服务
    netmiko_service = get_netmiko_service()
    
    success = False
    output = None
    error_message = None
    start_time = time.time()
    
    try:
        # 执行命令
        output = await netmiko_service.execute_command(device, command)
        success = True
        message = "命令执行成功"
    except Exception as e:
        error_message = str(e)
        success = False
        message = f"命令执行异常: {str(e)}"
    
    duration = time.time() - start_time
    
    # 保存命令执行历史
    history = CommandHistory(
        device_id=device_id,
        command=command,
        output=output,
        success=success,
        error_message=error_message,
        executed_by="system",  # 可以从认证信息中获取实际用户
        duration=duration
    )
    db.add(history)
    db.commit()
    
    return {
        "success": success,
        "message": message,
        "device_id": device_id,
        "hostname": device.hostname,
        "command": command,
        "output": output,
        "duration": duration
    }


@router.post("/batch/execute-command")
async def batch_execute_command(batch_request: BatchCommandExecutionRequest, db: Session = Depends(get_db)):
    """
    批量执行设备命令
    
    Args:
        batch_request: 批量命令执行请求
        db: SQLAlchemy会话
    
    Returns:
        批量命令执行结果
    """
    from app.models.models import CommandHistory
    import time
    
    device_ids = batch_request.device_ids
    base_command = batch_request.command
    variables = batch_request.variables or {}
    template_id = batch_request.template_id
    
    success_count = 0
    failed_count = 0
    results = []
    
    # 如果使用模板，获取模板
    from app.models.models import CommandTemplate
    template = None
    if template_id:
        template = db.query(CommandTemplate).filter(CommandTemplate.id == template_id).first()
    
    # 获取Netmiko服务
    netmiko_service = get_netmiko_service()
    
    for device_id in device_ids:
        try:
            # 获取设备信息
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                failed_count += 1
                results.append({
                    "device_id": device_id,
                    "hostname": "未知设备",
                    "success": False,
                    "message": "设备不存在"
                })
                continue
            
            # 确定最终命令
            command = base_command
            if template:
                # 使用模板命令并替换变量
                command = template.command
                for var_name, var_value in variables.items():
                    command = command.replace(f"{{{{{var_name}}}}}", str(var_value))
            
            # 执行命令
            start_time = time.time()
            output = await netmiko_service.execute_command(device, command)
            duration = time.time() - start_time
            
            if output is not None:
                success_count += 1
                success = True
                message = "命令执行成功"
            else:
                failed_count += 1
                success = False
                message = "命令执行失败"
                output = None
            
            # 保存命令执行历史
            history = CommandHistory(
                device_id=device_id,
                command=command,
                output=output,
                success=success,
                error_message=None if success else message,
                executed_by="system",
                duration=duration
            )
            db.add(history)
            
            results.append({
                "device_id": device_id,
                "hostname": device.hostname,
                "success": success,
                "message": message,
                "output": output,
                "duration": duration
            })
        except Exception as e:
            failed_count += 1
            error_message = str(e)
            results.append({
                "device_id": device_id,
                "hostname": device.hostname if 'device' in locals() else "未知设备",
                "success": False,
                "message": f"命令执行异常: {error_message}"
            })
            
            # 保存失败的命令执行历史
            if 'device' in locals() and device:
                history = CommandHistory(
                    device_id=device_id,
                    command=command if 'command' in locals() else base_command,
                    output=None,
                    success=False,
                    error_message=error_message,
                    executed_by="system",
                    duration=time.time() - start_time if 'start_time' in locals() else None
                )
                db.add(history)
    
    db.commit()
    
    return {
        "total": len(device_ids),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results
    }


@router.post("/batch/import", response_model=BatchOperationResult)
def batch_import_devices(
    file: UploadFile = File(...),
    skip_existing: bool = False,
    db: Session = Depends(get_db)
):
    """
    批量导入设备数据

    Args:
        file: Excel文件
        skip_existing: 是否跳过已存在的设备，False则更新
        db: SQLAlchemy会话

    Returns:
        导入结果统计
    """
    import traceback
    import logging

    logger = logging.getLogger(__name__)

    # 验证文件类型
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持.xlsx格式文件"
        )

    # 验证文件大小（限制10MB）
    max_file_size = 10 * 1024 * 1024  # 10MB
    file.file.seek(0, 2)  # 移动到文件末尾
    file_size = file.file.tell()
    file.file.seek(0)  # 重置到文件开头

    if file_size > max_file_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制（最大10MB）"
        )

    # 读取文件内容
    try:
        logger.info(f"开始批量导入设备，文件名: {file.filename}, 大小: {file_size} bytes")
        file_content = BytesIO(file.file.read())
        result = import_devices_from_excel(file_content, db, skip_existing=skip_existing)

        logger.info(f"批量导入完成: {result['success']} 成功, {result['skipped']} 跳过, {result['failed']} 失败")
        return BatchOperationResult(
            success=result['failed'] == 0,
            message=f"批量导入完成: {result['success']} 成功, {result['skipped']} 跳过, {result['failed']} 失败",
            total=result['total'],
            success_count=result['success'],
            failed_count=result['failed'],
            failed_devices=result['errors'] if result['errors'] else None
        )
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"导入失败: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
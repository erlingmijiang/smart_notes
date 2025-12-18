1. 在main\_async.py中导入asyncio库
2. 将main函数改为异步函数async def main
3. 使用asyncio.Semaphore(4)来限制并发数
4. 将同步函数调用（download\_bilibili\_audio、xf\_asr、llm\_inference）包装为await asyncio.to\_thread()
5. 修改main函数调用方式，使用asyncio.run()来运行主异步函数
6. 修改任务处理逻辑，使用asyncio.gather()或asyncio.create\_task()来并发执行多个任务
7. 保持原有功能不变，只修改为异步执行方式
8. 确保错误处理机制正常工作
9. 确保其他组件不要修改，若有必要修改其他py脚本，另行新建


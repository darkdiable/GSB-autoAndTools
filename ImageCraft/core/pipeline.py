import numpy as np
from typing import List, Callable, Optional
from .processor import ImageProcessor


class ProcessingPipeline:
    """图像处理流水线"""
    
    def __init__(self):
        self.steps: List[Callable] = []
        self.parameters: List[dict] = []
        self.processor: Optional[ImageProcessor] = None
    
    def add_step(self, operation: Callable, **kwargs) -> 'ProcessingPipeline':
        """添加处理步骤"""
        self.steps.append(operation)
        self.parameters.append(kwargs)
        return self
    
    def execute(self, processor: ImageProcessor) -> ImageProcessor:
        """执行流水线"""
        self.processor = processor
        
        for i, (step, params) in enumerate(zip(self.steps, self.parameters)):
            try:
                if params and 'image' in params:
                    result = step(**params)
                    if result is not None:
                        processor.image = result
                else:
                    params['image'] = processor.image
                    result = step(**params)
                    if result is not None:
                        processor.image = result
            except Exception as e:
                raise RuntimeError(f"步骤 {i+1} 执行失败：{e}")
        
        return processor
    
    def clear(self) -> None:
        """清空流水线"""
        self.steps = []
        self.parameters = []
    
    def get_steps(self) -> List[str]:
        """获取所有步骤名称"""
        return [step.__name__ for step in self.steps]
    
    def validate(self) -> bool:
        """验证流水线是否有效"""
        if len(self.steps) == 0:
            return False
        
        for step in self.steps:
            if not callable(step):
                return False
        
        return True
    
    def save_pipeline(self, path: str) -> None:
        """保存流水线配置"""
        import json
        
        config = {
            'steps': [step.__name__ for step in self.steps],
            'parameters': self.parameters
        }
        
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_pipeline(self, path: str, operations: dict) -> None:
        """加载流水线配置"""
        import json
        
        with open(path, 'r') as f:
            config = json.load(f)
        
        self.steps = []
        self.parameters = []
        
        for step_name, params in zip(config['steps'], config['parameters']):
            if step_name in operations:
                self.steps.append(operations[step_name])
                self.parameters.append(params)


def create_pipeline() -> ProcessingPipeline:
    """创建新的流水线"""
    return ProcessingPipeline()

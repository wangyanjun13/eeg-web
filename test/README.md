# EEG-Web系统性能测试与可视化套件

本套件提供了一系列工具，用于从EEG-Web系统收集实际性能数据并生成高质量可视化图表，以便进行系统评估和展示。

## 目录结构

```
eeg-web/test/
├── data/                     # 测试数据存储目录
├── results/                  # 生成的可视化图表保存目录
├── api_routes_example.py     # API路由参考（已集成到系统）
├── run_all_tests.py          # 主数据收集与可视化脚本
├── test_api.py               # API端点测试脚本
├── README.md                 # 本文档
├── test_1_mne_comparison.py     # MNE对比散点图生成脚本
├── test_2_preprocessing_performance.py  # 预处理性能柱状图生成脚本
├── test_3_multimodal_analysis.py  # 多模态分析可视化示例图生成脚本
├── test_4_hardware_performance.py  # 硬件性能箱线图生成脚本
├── test_5_response_time.py  # 响应时间热力图生成脚本
├── test_6_concurrency.py  # 并发性能曲面图生成脚本
└── test_7_resource_usage.py  # 资源使用率时序图生成脚本
```

## 快速开始

### 步骤1：准备环境

确保您已经创建了必要的目录：

```bash
mkdir -p eeg-web/results
mkdir -p eeg-web/test/data
```

### 步骤2：启动EEG-Web系统

在测试前，确保您的EEG-Web系统已经启动：

### 步骤3：测试API端点

首先测试系统性能API端点是否正常工作：

```bash
cd eeg-web
python test/test_api.py
```

如果所有端点测试通过，您将看到成功消息，并且数据文件将保存在 `testing_data/`目录中。

### 步骤4：运行性能测试和可视化

运行完整的性能测试和可视化生成脚本：

```bash
cd eeg-web
python test/run_all_tests.py
```

脚本将：

1. 从API收集性能数据
2. 保存数据到 `eeg-web/test/data/`目录
3. 生成可视化图表保存到 `eeg-web/results/`目录

### 步骤5：查看结果

生成的可视化图表将保存在 `testing_results/`目录中，包括：

1. **图5.2_MNE相关性散点图.png** - 系统与MNE-Python的分析结果对比
2. **图5.3_预处理性能对比.png** - 预处理性能柱状图
3. **图5.5_多模态分析.png** - 多模态分析可视化示例图
4. **图5.6_交互帧率箱线图.png** - 不同硬件配置下的交互帧率箱线图
5. **图5.7_响应时间热力图.png** - 系统响应时间分布热力图
6. **图5.8_并发性能曲面.png** - 并发性能测试结果曲面图
7. **图5.9_资源利用率.png** - 资源使用率时序分布图

## API端点说明

本套件使用以下API端点收集系统性能数据：

1. `/api/system/mne-comparison` - 系统与MNE-Python的分析结果对比数据
2. `/api/system/preprocess/performance` - 预处理性能数据
3. `/api/system/analysis/multimodal` - 多模态分析数据
4. `/api/system/hardware-performance` - 硬件性能数据
5. `/api/system/response-times` - 系统响应时间数据
6. `/api/system/concurrency` - 并发性能数据
7. `/api/system/resource-usage` - 系统资源使用数据

这些API端点已经集成到EEG-Web系统中，由 `app/api/system.py`模块提供。

## 自定义测试

### 修改API基础URL

如果您的EEG-Web系统不在默认地址上运行，请修改 `run_all_tests.py`和 `test_api.py`文件中的API基础URL：

```python
API_BASE_URL = "http://localhost:8000"  # 修改为您的实际地址
```

### 使用真实数据

默认情况下，API端点提供模拟数据。要使用真实系统数据，您需要修改 `app/api/system.py`文件中的相应端点实现，连接到您的真实数据源。

### 自定义可视化

您可以修改各个测试脚本中的可视化参数，如颜色、大小、标签等，以适应您的需求。

## 故障排除

### API连接问题

如果无法连接到API：

1. 确保EEG-Web系统正在运行
2. 检查API地址是否正确
3. 检查网络连接和防火墙设置

### 可视化问题

如果可视化生成失败：

1. 检查Python环境是否安装了所有必要的库（matplotlib, seaborn等）
2. 检查数据格式是否正确
3. 检查目录权限是否正确

## 依赖项

- Python 3.7+
- requests
- numpy
- matplotlib
- seaborn
- pandas
- FastAPI (后端)
- psutil

## 注意事项

- 模拟数据：目前系统使用模拟数据，您可以根据需要将其替换为实际系统数据
- 性能影响：运行完整测试可能会对系统性能产生影响，建议在非生产环境中进行测试
- 数据安全：确保您的测试环境安全，不要在公共环境中暴露敏感性能数据

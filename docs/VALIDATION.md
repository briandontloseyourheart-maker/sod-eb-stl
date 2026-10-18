# 构建与验证记录（2026-10-18）

本工程基于 ../sod_eb2 的 C++ CNS；src 文件与该基线完全相同，实际差异是输入几何从解析 sphere 改为 binary STL，以及构建/运行/验证工具。源码来源见 provenance.json；原许可证见 LICENSE-AMReX。

## 执行命令

```bash
python3 tools/generate_sphere.py
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
  -DAMReX_DIR=/home/xiaohui/codes/myamrex_5/sod_eb2/build/amrex/lib/cmake/AMReX
cmake --build build -j 8
ctest --test-dir build --output-on-failure
python3 tools/run.py --output results/sphere_stl --threads 4
MPLCONFIGDIR=/tmp/sod-stl-mpl python3 tools/plot.py results/sphere_stl
python3 tools/compare.py results/sphere_stl ../sod_eb2/results/sphere
```

上述构建、测试、运行、绘图和比较均通过。额外验证了默认 add_subdirectory 源码路径的 CMake 配置成功（/tmp/sod-stl-source-configure）；没有在这个额外目录重复编译 AMReX。Python 脚本语法检查通过；ParaView 脚本尚未在用户的 Windows ParaView 中执行。

## 几何验证

球心 (0.7,0.5,0.5)，半径 0.125。binary STL 含 16128 个三角形，无退化面，封闭双流形、相邻边方向一致、法向向外。STL 体积相对解析球误差 0.10036%；这是三角面逼近误差。

运行日志明确记录 `Reading binary STL file sphere.stl`、16128 三角形及正确包围盒，未回退到 sphere 几何。运行目录 STL 的 SHA256 在 run.json 中，与 geometry/audit.json 相同。

## 完整运行

- 64³ 粗网格，最大 Level 1（2倍细化），CPU 4 OpenMP 线程。
- 程序退出码 0，102 个粗步到 t=0.2，7 个三维 plotfile。
- 本次总耗时约 132.8 秒，仅为环境观测，不作为性能结论。
- 4788 个复合 EB 切割单元；EB 离散固体体积相对解析球误差约 0.29395%，包含 STL 与切割网格两部分误差。
- 最小密度 0.122577、最小压力 0.096432，有效流体状态均有限且为正。
- 质量最大相对变化 9.15e-12，总能量最大相对变化 8.26e-12。复合统计去除细层覆盖的粗单元，乘以实际流体体积分数。

## 与解析 sphere 比较

在同一 t=0.2，将两种复合切片按分片常值投到 128×128 网格，统计共同流体区域：

| 变量 | 平均绝对差 | 最大绝对差 |
|---|---:|---:|
| 密度 | 1.9704e-5 | 0.003784 |
| 压力 | 2.3594e-5 | 0.006106 |

两种切片的纯固体/流体像素分类一致，但体积分数可能不同。此比较是同一基准的几何表示敏感性检查；两种结果均为数值解，没有将解析 sphere 流场当作精确解。这里只比较了单元中心切片，并非完整三维误差范数，也没有完成网格/三角面收敛研究。

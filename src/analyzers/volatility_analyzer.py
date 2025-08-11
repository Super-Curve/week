#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

class VolatilityAnalyzer:
    """
    波动率与波幅分析器

    用途:
    - 提供历史/已实现/Parkinson/Garman-Klass 等多种波动率计算，以及日内/期间波幅测度。

    实现方式:
    - 基于 pandas 滚动窗口与闭式近似公式计算；统一年化到周频52

    优点:
    - 指标覆盖充分；与 HTML/图表接口解耦

    局限:
    - 依赖数据质量（高低价异常会放大噪声）；不做缺失自动修复

    维护建议:
    - 新增估计器请保持函数签名一致；统一在 analyze_stock_volatility 中汇总输出
    """
    
    def __init__(self):
        self.risk_free_rate = 0.03  # 无风险利率，默认3%
    
    def calculate_historical_volatility(self, prices: pd.Series, window: int = 20) -> pd.Series:
        """
        计算历史波动率
        
        Args:
            prices: 价格序列
            window: 计算窗口（默认20个周期）
            
        Returns:
            历史波动率序列
        """
        # 计算对数收益率
        returns = np.log(prices / prices.shift(1))
        
        # 计算滚动标准差
        volatility = returns.rolling(window=window).std() * np.sqrt(52)  # 年化（假设周数据）
        
        return volatility
    
    def calculate_intraday_amplitude(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """
        计算日内波幅
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            
        Returns:
            日内波幅序列
        """
        amplitude = (high - low) / close * 100
        return amplitude
    
    def calculate_period_amplitude(self, prices: pd.Series, window: int = 20) -> pd.Series:
        """
        计算期间波幅
        
        Args:
            prices: 价格序列
            window: 计算窗口
            
        Returns:
            期间波幅序列
        """
        rolling_max = prices.rolling(window=window).max()
        rolling_min = prices.rolling(window=window).min()
        rolling_mean = prices.rolling(window=window).mean()
        
        amplitude = (rolling_max - rolling_min) / rolling_mean * 100
        return amplitude
    
    def calculate_realized_volatility(self, returns: pd.Series, window: int = 20) -> pd.Series:
        """
        计算已实现波动率
        
        Args:
            returns: 收益率序列
            window: 计算窗口
            
        Returns:
            已实现波动率序列
        """
        realized_vol = returns.rolling(window=window).apply(
            lambda x: np.sqrt(np.sum(x**2) / len(x)) * np.sqrt(52)
        )
        return realized_vol
    
    def calculate_parkinson_volatility(self, high: pd.Series, low: pd.Series, window: int = 20) -> pd.Series:
        """
        计算Parkinson波动率（基于高低价）
        
        Args:
            high: 最高价序列
            low: 最低价序列
            window: 计算窗口
            
        Returns:
            Parkinson波动率序列
        """
        log_hl = np.log(high / low)
        parkinson_vol = log_hl.rolling(window=window).apply(
            lambda x: np.sqrt(np.sum(x**2) / (4 * np.log(2) * len(x))) * np.sqrt(52)
        )
        return parkinson_vol
    
    def calculate_garman_klass_volatility(self, open_price: pd.Series, high: pd.Series, 
                                        low: pd.Series, close: pd.Series, window: int = 20) -> pd.Series:
        """
        计算Garman-Klass波动率
        
        Args:
            open_price: 开盘价序列
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            window: 计算窗口
            
        Returns:
            Garman-Klass波动率序列
        """
        log_hl = np.log(high / low)
        log_co = np.log(close / open_price)
        
        gk_vol = (0.5 * log_hl**2 - (2*np.log(2) - 1) * log_co**2).rolling(window=window).apply(
            lambda x: np.sqrt(np.sum(x) / len(x)) * np.sqrt(52)
        )
        return gk_vol
    
    def analyze_stock_volatility(self, stock_data: pd.DataFrame, 
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> Dict:
        """
        分析股票的波动率和波幅
        
        Args:
            stock_data: 股票数据DataFrame
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            分析结果字典
        """
        # 过滤时间范围
        if start_date:
            stock_data = stock_data[stock_data.index >= start_date]
        if end_date:
            stock_data = stock_data[stock_data.index <= end_date]
        
        if len(stock_data) < 20:
            return {"error": "数据不足，至少需要20个数据点"}
        
        # 计算各种波动率指标
        close_prices = stock_data['close']
        high_prices = stock_data['high']
        low_prices = stock_data['low']
        open_prices = stock_data['open']
        
        # 计算收益率
        returns = np.log(close_prices / close_prices.shift(1))
        
        # 计算各种波动率
        hist_vol_20 = self.calculate_historical_volatility(close_prices, 20)
        hist_vol_60 = self.calculate_historical_volatility(close_prices, 60)
        realized_vol = self.calculate_realized_volatility(returns, 20)
        parkinson_vol = self.calculate_parkinson_volatility(high_prices, low_prices, 20)
        gk_vol = self.calculate_garman_klass_volatility(open_prices, high_prices, low_prices, close_prices, 20)
        
        # 计算波幅
        intraday_amp = self.calculate_intraday_amplitude(high_prices, low_prices, close_prices)
        period_amp_20 = self.calculate_period_amplitude(close_prices, 20)
        period_amp_60 = self.calculate_period_amplitude(close_prices, 60)
        
        # 计算统计指标
        current_vol = hist_vol_20.iloc[-1] if not pd.isna(hist_vol_20.iloc[-1]) else 0
        avg_vol = hist_vol_20.mean()
        vol_percentile = (hist_vol_20 < current_vol).mean() * 100
        
        current_amp = intraday_amp.iloc[-1] if not pd.isna(intraday_amp.iloc[-1]) else 0
        avg_amp = intraday_amp.mean()
        amp_percentile = (intraday_amp < current_amp).mean() * 100
        
        return {
            "data": {
                "dates": [str(d) for d in stock_data.index.tolist()],
                "close_prices": close_prices.tolist(),
                "hist_vol_20": hist_vol_20.tolist(),
                "hist_vol_60": hist_vol_60.tolist(),
                "realized_vol": realized_vol.tolist(),
                "parkinson_vol": parkinson_vol.tolist(),
                "gk_vol": gk_vol.tolist(),
                "intraday_amp": intraday_amp.tolist(),
                "period_amp_20": period_amp_20.tolist(),
                "period_amp_60": period_amp_60.tolist()
            },
            "statistics": {
                "current_volatility": round(current_vol, 4),
                "average_volatility": round(avg_vol, 4),
                "volatility_percentile": round(vol_percentile, 2),
                "current_amplitude": round(current_amp, 2),
                "average_amplitude": round(avg_amp, 2),
                "amplitude_percentile": round(amp_percentile, 2),
                "max_volatility": round(hist_vol_20.max(), 4),
                "min_volatility": round(hist_vol_20.min(), 4),
                "max_amplitude": round(intraday_amp.max(), 2),
                "min_amplitude": round(intraday_amp.min(), 2)
            },
            "risk_level": self._assess_risk_level(current_vol, current_amp, vol_percentile, amp_percentile)
        }
    
    def _assess_risk_level(self, vol: float, amp: float, vol_percentile: float, amp_percentile: float) -> str:
        """评估风险等级"""
        if vol_percentile > 80 and amp_percentile > 80:
            return "高风险"
        elif vol_percentile > 60 or amp_percentile > 60:
            return "中高风险"
        elif vol_percentile < 20 and amp_percentile < 20:
            return "低风险"
        else:
            return "中等风险"
    
    def generate_volatility_chart(self, analysis_result: Dict, output_path: str):
        """生成波动率分析图表"""
        if "error" in analysis_result:
            return False
        
        data = analysis_result["data"]
        stats = analysis_result["statistics"]
        
        fig, axes = plt.subplots(3, 2, figsize=(15, 12))
        fig.suptitle('股票波动率和波幅分析', fontsize=16, fontweight='bold')
        
        # 优化横坐标显示
        def optimize_xaxis(ax, dates):
            """优化横坐标显示，避免标签重叠"""
            # 选择合适数量的日期标签
            n_dates = len(dates)
            if n_dates <= 10:
                step = 1
            elif n_dates <= 20:
                step = 2
            elif n_dates <= 50:
                step = 5
            else:
                step = max(1, n_dates // 10)
            
            # 设置x轴标签
            ax.set_xticks(range(0, n_dates, step))
            ax.set_xticklabels([dates[i] for i in range(0, n_dates, step)], 
                              rotation=45, ha='right', fontsize=8)
            
            # 调整布局避免标签被截断
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # 价格走势
        axes[0, 0].plot(range(len(data["dates"])), data["close_prices"], 'b-', linewidth=1)
        axes[0, 0].set_title('价格走势')
        axes[0, 0].set_ylabel('价格')
        axes[0, 0].grid(True, alpha=0.3)
        optimize_xaxis(axes[0, 0], data["dates"])
        
        # 历史波动率
        axes[0, 1].plot(range(len(data["dates"])), data["hist_vol_20"], 'r-', label='20周期', linewidth=1)
        axes[0, 1].plot(range(len(data["dates"])), data["hist_vol_60"], 'g-', label='60周期', linewidth=1)
        axes[0, 1].set_title('历史波动率')
        axes[0, 1].set_ylabel('波动率')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        optimize_xaxis(axes[0, 1], data["dates"])
        
        # 不同波动率指标对比
        axes[1, 0].plot(range(len(data["dates"])), data["realized_vol"], 'b-', label='已实现波动率', linewidth=1)
        axes[1, 0].plot(range(len(data["dates"])), data["parkinson_vol"], 'r-', label='Parkinson波动率', linewidth=1)
        axes[1, 0].plot(range(len(data["dates"])), data["gk_vol"], 'g-', label='Garman-Klass波动率', linewidth=1)
        axes[1, 0].set_title('波动率指标对比')
        axes[1, 0].set_ylabel('波动率')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        optimize_xaxis(axes[1, 0], data["dates"])
        
        # 日内波幅
        axes[1, 1].plot(range(len(data["dates"])), data["intraday_amp"], 'purple', linewidth=1)
        axes[1, 1].set_title('日内波幅')
        axes[1, 1].set_ylabel('波幅 (%)')
        axes[1, 1].grid(True, alpha=0.3)
        optimize_xaxis(axes[1, 1], data["dates"])
        
        # 期间波幅
        axes[2, 0].plot(range(len(data["dates"])), data["period_amp_20"], 'orange', label='20周期', linewidth=1)
        axes[2, 0].plot(range(len(data["dates"])), data["period_amp_60"], 'brown', label='60周期', linewidth=1)
        axes[2, 0].set_title('期间波幅')
        axes[2, 0].set_ylabel('波幅 (%)')
        axes[2, 0].legend()
        axes[2, 0].grid(True, alpha=0.3)
        optimize_xaxis(axes[2, 0], data["dates"])
        
        # 统计信息和计算方式介绍
        axes[2, 1].axis('off')
        
        # 创建两个文本框：统计信息和计算方式
        stats_text = f"""
📊 统计信息
当前波动率: {stats['current_volatility']}
平均波动率: {stats['average_volatility']}
波动率百分位: {stats['volatility_percentile']}%

当前波幅: {stats['current_amplitude']}%
平均波幅: {stats['average_amplitude']}%
波幅百分位: {stats['amplitude_percentile']}%

风险等级: {analysis_result['risk_level']}
        """
        
        formula_text = """
📈 波动率计算方式

1. 历史波动率:
   σ = std(ln(Pt/Pt-1)) × √52

2. 已实现波动率:
   σ = √(Σ(rt²)/n) × √52

3. Parkinson波动率:
   σ = √(Σ(ln(Ht/Lt)²)/(4×ln(2)×n)) × √52

4. Garman-Klass波动率:
   σ = √(Σ(0.5×ln(Ht/Lt)²-(2×ln(2)-1)×ln(Ct/Ot)²)/n) × √52

其中: Pt=价格, rt=收益率, Ht=最高价, Lt=最低价, Ct=收盘价, Ot=开盘价
        """
        
        # 左侧显示统计信息
        axes[2, 1].text(0.05, 0.95, stats_text, transform=axes[2, 1].transAxes, 
                       fontsize=10, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        # 右侧显示计算方式
        axes[2, 1].text(0.55, 0.95, formula_text, transform=axes[2, 1].transAxes, 
                       fontsize=8, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return True 
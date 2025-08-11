"""
A股形态识别系统主程序
演示如何使用各模块进行形态识别和信号生成
"""

import pandas as pd
import numpy as np
import yaml
from datetime import datetime
import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from indicators.volatility import VolatilityIndicators
from pattern_recognition.swing_points import SwingPointDetector
from trading.signal_generator import SignalGenerator


class PatternRecognitionSystem:
    """A股形态识别系统主类"""
    
    def __init__(self, config_path: str = 'config/config.yaml'):
        """初始化系统"""
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
            
        # 初始化各模块
        self.volatility_calculator = VolatilityIndicators()
        self.swing_detector = SwingPointDetector(
            lookback_window=self.config['pattern_recognition']['lookback_window'],
            volatility_factor=self.config['volatility']['filter_factor'],
            time_confirm=self.config['pattern_recognition']['time_confirm'],
            volume_factor=self.config['pattern_recognition']['volume_factor']
        )
        self.signal_generator = SignalGenerator(self.config['trading'])
        
    def load_data(self, stock_code: str, start_date: str = None, 
                  end_date: str = None) -> pd.DataFrame:
        """
        加载股票数据（这里使用模拟数据作为示例）
        实际使用时应该从数据源加载真实数据
        """
        # 生成模拟数据用于演示
        dates = pd.date_range(start=start_date or '2023-01-01', 
                             end=end_date or '2024-01-01', freq='D')
        
        # 模拟价格走势
        np.random.seed(42)
        base_price = 10.0
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = base_price * np.exp(np.cumsum(returns))
        
        # 生成OHLCV数据
        data = pd.DataFrame(index=dates)
        data['close'] = prices
        data['open'] = prices * (1 + np.random.normal(0, 0.005, len(dates)))
        data['high'] = np.maximum(data['open'], data['close']) * (1 + np.abs(np.random.normal(0, 0.01, len(dates))))
        data['low'] = np.minimum(data['open'], data['close']) * (1 - np.abs(np.random.normal(0, 0.01, len(dates))))
        data['volume'] = np.random.lognormal(15, 0.5, len(dates))
        
        print(f"数据加载完成: {stock_code}")
        print(f"日期范围: {data.index[0]} 到 {data.index[-1]}")
        print(f"数据行数: {len(data)}")
        
        return data
    
    def analyze_stock(self, stock_code: str, data: pd.DataFrame = None):
        """
        分析单只股票
        """
        print(f"\n{'='*50}")
        print(f"开始分析股票: {stock_code}")
        print(f"{'='*50}")
        
        # 如果没有提供数据，则加载数据
        if data is None:
            data = self.load_data(
                stock_code,
                self.config['data_source']['start_date'],
                self.config['data_source']['end_date']
            )
        
        # 1. 计算波动率指标
        print("\n1. 计算波动率指标...")
        atr = self.volatility_calculator.calculate_atr(
            data['high'], data['low'], data['close'],
            self.config['volatility']['atr_period']
        )
        
        atr_pct = self.volatility_calculator.calculate_atr_percent(
            data['high'], data['low'], data['close'],
            self.config['volatility']['atr_period']
        )
        
        dynamic_vol = self.volatility_calculator.calculate_dynamic_volatility(
            data['high'], data['low'], data['close'],
            self.config['volatility']['atr_period'],
            self.config['volatility']['hv_period'],
            self.config['volatility']['bb_period']
        )
        
        print(f"  - ATR平均值: {atr.mean():.4f}")
        print(f"  - ATR百分比平均值: {atr_pct.mean():.2f}%")
        
        # 2. 识别高低点
        print("\n2. 识别高低点...")
        swing_points = self.swing_detector.detect_swing_points(data, atr_pct)
        
        print(f"  - 识别到的高点数量: {len(swing_points['highs'])}")
        print(f"  - 识别到的低点数量: {len(swing_points['lows'])}")
        
        # 显示最近的几个高低点
        if swing_points['highs']:
            print("\n  最近的高点:")
            for high in swing_points['highs'][-3:]:
                print(f"    {high.date.strftime('%Y-%m-%d')}: {high.price:.2f} "
                      f"(波动率: {high.volatility:.2f}%, 确认: {high.confirmed})")
        
        if swing_points['lows']:
            print("\n  最近的低点:")
            for low in swing_points['lows'][-3:]:
                print(f"    {low.date.strftime('%Y-%m-%d')}: {low.price:.2f} "
                      f"(波动率: {low.volatility:.2f}%, 确认: {low.confirmed})")
        
        # 3. 识别形态
        print("\n3. 识别形态模式...")
        patterns = self.swing_detector.identify_patterns(swing_points)
        
        if patterns:
            print(f"  - 识别到 {len(patterns)} 个形态")
            for pattern in patterns:
                print(f"    {pattern['type']}: {pattern['start_date'].strftime('%Y-%m-%d')} "
                      f"到 {pattern['end_date'].strftime('%Y-%m-%d')}")
                if 'target' in pattern:
                    print(f"      目标价: {pattern['target']:.2f}")
        else:
            print("  - 未识别到明显形态")
        
        # 4. 生成交易信号
        print("\n4. 生成交易信号...")
        signals = self.signal_generator.generate_signals(
            data, swing_points, dynamic_vol, atr, patterns
        )
        
        if signals:
            print(f"  - 生成 {len(signals)} 个交易信号")
            # 显示最近的几个信号
            for signal in signals[-5:]:
                print(f"    {signal.date.strftime('%Y-%m-%d')}: {signal.signal_type.value} "
                      f"@ {signal.price:.2f}")
                print(f"      理由: {signal.reason}")
                print(f"      止损: {signal.stop_loss:.2f}, 止盈: {signal.take_profit:.2f}")
                print(f"      置信度: {signal.confidence:.2f}, 仓位: {signal.position_size:.2%}")
        else:
            print("  - 暂无交易信号")
        
        # 5. 当前支撑阻力位
        print("\n5. 当前关键价位...")
        current_levels = self.swing_detector.get_swing_levels(swing_points, len(data) - 1)
        
        if current_levels['resistance']:
            print(f"  - 阻力位: {current_levels['resistance']:.2f}")
        if current_levels['support']:
            print(f"  - 支撑位: {current_levels['support']:.2f}")
        
        return {
            'data': data,
            'swing_points': swing_points,
            'patterns': patterns,
            'signals': signals,
            'volatility': {
                'atr': atr,
                'atr_pct': atr_pct,
                'dynamic': dynamic_vol
            }
        }
    
    def analyze_multiple_stocks(self, stock_codes: list):
        """分析多只股票"""
        results = {}
        
        for code in stock_codes:
            try:
                results[code] = self.analyze_stock(code)
            except Exception as e:
                print(f"分析股票 {code} 时出错: {str(e)}")
                
        return results


def main():
    """主函数"""
    print("A股形态识别系统启动")
    print("=" * 70)
    
    # 创建系统实例
    system = PatternRecognitionSystem()
    
    # 分析示例股票
    # 实际使用时替换为真实的股票代码
    stock_codes = ['600000', '000001', '000002']
    
    # 分析单只股票详细信息
    result = system.analyze_stock(stock_codes[0])
    
    # 分析多只股票
    # results = system.analyze_multiple_stocks(stock_codes)
    
    print("\n" + "=" * 70)
    print("分析完成！")
    
    # 保存结果（可选）
    # 这里可以添加将结果保存到文件或数据库的代码
    

if __name__ == "__main__":
    main()
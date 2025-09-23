# MySQL
datasource.url=jdbc:mysql://rm-0jl8p6ell797x1h5ozo.mysql.rds.aliyuncs.com:3308/lianghua?serverTimezone=Asia/Shanghai&useUnicode=true&characterEncoding=UTF-8
datasource.username=lianghua
datasource.password=Aa123456

CREATE TABLE `stock_info` (
  `stock_code` varchar(10) NOT NULL COMMENT '股票代码',
  `stock_name` varchar(16) NOT NULL COMMENT '股票名称',
  `total_market_value` varchar(32) DEFAULT NULL COMMENT '总市值',
  `industry` varchar(16) DEFAULT NULL COMMENT '行业分类',
  `ipo_date` varchar(16) DEFAULT NULL COMMENT '上市日期'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='股票代码信息表';

CREATE TABLE `history_week_data` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增主键ID',
  `trade_date` date NOT NULL COMMENT '交易日期（格式：2025/07/04）',
  `code` varchar(16) NOT NULL COMMENT '股票代码',
  `open` varchar(16) DEFAULT NULL COMMENT '开盘价',
  `high` varchar(16) DEFAULT NULL COMMENT '最高价',
  `low` varchar(16) DEFAULT NULL COMMENT '最低价',
  `close` varchar(16) DEFAULT NULL COMMENT '收盘价',
  PRIMARY KEY (`id`),
  KEY `idx_trade_code` (`code`,`trade_date`)
) ENGINE=InnoDB AUTO_INCREMENT=1548983 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='股票历史周表';

CREATE TABLE `history_day_data` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增主键ID',
  `trade_date` date NOT NULL COMMENT '交易日期（格式：2025/07/04）',
  `code` varchar(16) NOT NULL COMMENT '股票代码',
  `open` varchar(16) DEFAULT NULL COMMENT '开盘价',
  `high` varchar(16) DEFAULT NULL COMMENT '最高价',
  `low` varchar(16) DEFAULT NULL COMMENT '最低价',
  `close` varchar(16) DEFAULT NULL COMMENT '收盘价',
  PRIMARY KEY (`id`),
  KEY `idx_trade_code` (`code`,`trade_date`)
) ENGINE=InnoDB AUTO_INCREMENT=7389919 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='股票历史日表';

-- 统一策略标的池表（按 dt 取最新记录）
CREATE TABLE IF NOT EXISTS `strategy_candidates` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `dt` DATE NOT NULL COMMENT '结果日期(yyyy-mm-dd)，查询取 MAX(dt)',
  `strategy_type` VARCHAR(32) NOT NULL COMMENT '策略类型：long_term / short_term / ...',
  `code` VARCHAR(16) NOT NULL COMMENT '股票代码',
  `name` VARCHAR(64) DEFAULT NULL COMMENT '股票名称',
  `market_cap_category` VARCHAR(16) DEFAULT NULL COMMENT '小盘股/中盘股/大盘股',
  `market_value_bil` DECIMAL(12,2) DEFAULT NULL COMMENT '总市值(亿元)',
  `ipo_date` DATE DEFAULT NULL COMMENT '上市日期',
  `volatility_annualized` DECIMAL(9,6) DEFAULT NULL COMMENT '年化/窗口化波动率(0-1)',
  `sharpe_ratio` DECIMAL(9,6) DEFAULT NULL COMMENT '夏普比',
  `rank_in_dt` INT DEFAULT NULL COMMENT '同日排名(从1开始)',
  `score` DECIMAL(9,6) DEFAULT NULL COMMENT '综合评分(可选)',
  `t2_date` DATE DEFAULT NULL COMMENT 'T2日期(如有)',
  `entry_date` DATE DEFAULT NULL COMMENT '入场日期(如有)',
  `entry_price` DECIMAL(12,4) DEFAULT NULL COMMENT '入场价格(如有)',
  `data_frequency` ENUM('daily','weekly','mixed') DEFAULT NULL COMMENT '度量频率',
  `data_window_days` INT DEFAULT NULL COMMENT '度量窗口(天)',
  `extras` JSON NULL COMMENT '扩展指标/解释(JSON)',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dt_type_code` (`dt`,`strategy_type`,`code`),
  KEY `idx_type_dt_rank` (`strategy_type`,`dt`,`rank_in_dt`),
  KEY `idx_code_type` (`code`,`strategy_type`),
  KEY `idx_dt` (`dt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='统一策略标的池（按dt查询最新）';

-- 统一高低点明细（与策略无关，仅按股票维度）
CREATE TABLE IF NOT EXISTS `pivot_points` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `dt` DATE NOT NULL COMMENT '结果日期(yyyy-mm-dd)，查询取 MAX(dt)',
  `code` VARCHAR(16) NOT NULL COMMENT '股票代码',
  `data_frequency` VARCHAR(16) NOT NULL COMMENT '数据频率：daily/weekly',
  `is_filtered` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1=过滤后的转折点，0=原始点',
  `is_high` TINYINT(1) NOT NULL COMMENT '1=高点，0=低点',
  `trade_date` DATE NOT NULL COMMENT '转折点对应K线的日期',
  `bar_index` INT DEFAULT NULL COMMENT '该点在用于分析的序列中的索引（可选）',
  `price` DECIMAL(12,4) NOT NULL COMMENT '价格',
  `prominence` DECIMAL(12,6) DEFAULT NULL COMMENT '显著性/突出度（如有）',
  `confirm_strength` DECIMAL(12,6) DEFAULT NULL COMMENT '确认强度（如有）',
  `z_score` DECIMAL(12,6) DEFAULT NULL COMMENT '标准分（如有）',
  `atr_pct` DECIMAL(12,6) DEFAULT NULL COMMENT 'ATR占比阈值（如有）',
  `extras` JSON NULL COMMENT '其他算法指标与解释(阈值、过滤原因、质量分级等)',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dt_code_freq_filtered_high_date` (`dt`,`code`,`data_frequency`,`is_filtered`,`is_high`,`trade_date`),
  KEY `idx_code_dt` (`code`,`dt`),
  KEY `idx_code_date` (`code`,`trade_date`),
  KEY `idx_dt` (`dt`),
  KEY `idx_code_freq_dt` (`code`,`data_frequency`,`dt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='统一高低点明细（与策略无关，仅按股票维度）';

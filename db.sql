# MySQL
datasource.url=jdbc:mysql://rm-0jl8p6ell797x1h5ozo.mysql.rds.aliyuncs.com:3308/lianghua?serverTimezone=Asia/Shanghai&useUnicode=true&characterEncoding=UTF-8
datasource.username=lianghua
datasource.password=Aa123456

CREATE TABLE `stock_name` (
  `stock_code` varchar(10) NOT NULL COMMENT '股票代码',
  `stock_name` varchar(16) NOT NULL COMMENT '股票名称'
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

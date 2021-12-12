class StrategyConfigMessage:
    def __init__(self, jsondata):
        self.strategy_type          = jsondata["Type"]
        self.symbol                 = jsondata["Symbol"]
        self.client_id              = jsondata["clinet-details"]["Client-Id"]
        self.strategy_plugin        = jsondata["clinet-details"]["Strategy-Plugin"]
        self.client_api_key         = jsondata["clinet-details"]["Client-Api-Key"]
        self.client_api_key2        = jsondata["clinet-details"]["Client-Api-Key2"]
        self.enabled                = jsondata["clinet-details"]["Enabled"]
        self.exchange_enabled       = jsondata["clinet-details"]["Exchange-Enabled"]
        self.market_data_topic      = jsondata["Kafka-Details"]["Kafka-Topic-Mkt-Data"]
        self.config_update_topic    = jsondata["Kafka-Details"]["Kafka-Topic-Config-Update"]
        self.kafka_topic_admin      = jsondata["Kafka-Details"]["Kafka-Topic-Admin"]
        self.qty_unit               = float(jsondata["Configuration"]["QtyUnit"])
        self.qty_lvl_zero_qty       =  float(jsondata["Configuration"]["Lvl0Qty"])
        self.exit_percentage       =  float(jsondata["Configuration"]["ExitPct"])
        self.levels = []
        for strategy_data in jsondata["Configuration"]["levels"]:
            self.levels.append((float(strategy_data["Percentage"]), float(strategy_data["Qty"])))
        self.is_initialized = False
        self.entry_price = 0.0
        self.balance = 0.0


import drift_api.orders
import drift_api.market_data

class Strategy:
    def __init__(self, config):
        #Initialize based on relevant strategy parameters
        pass

    def update(self):
        #Apply new market parameters to strategy
        #apply_risk_management(self)
        pass

    def apply_risk_management(self):
        """
        Applies risk management rules to determine whether to adjust the position size, and by how much.
        """
        if self.desired_position_size != self.current_position_size:
            # If desired and current position sizes are different, adjust position size
            self.update_risk_parameters()
            self.calculate_desired_position_size()
            self.adjust_position_size()

    def update_risk_parameters(self):
        """
        Updates the risk management parameters based on market data.
        """
        self.market_data.update_market_data()
        self.market_data.get_dlob_data()
        self.market_data.update_volatility()

    def determine_bid_price(self):
        """
        Determines the bid price based on market data and the trading strategy.
        """
        pass

    def determine_ask_price(self):
        """
        Determines the ask price based on market data and the trading strategy.
        """
        pass

    def update_order_book(self):
        """
        Updates the order book with new orders and adjusts/cancels existing orders as necessary.
        """
        self.orders.update_orders()
        # Check if current bid/ask prices are outside the spread of existing orders
        # ...

        # Cancel orders if necessary
        # ...

        # Submit new orders if necessary
        # ...

    def place_orders(self):
        """
        Places orders based on the current bid/ask prices and desired position size.
        """
        pass

    def calculate_desired_position_size(self):
        """
        Calculates the desired position size based on the current market data and risk management rules.
        Pseudocode
        prices = []
        factor = aggression * asset_weight_discount if side == Side.BUY else aggression * 1.01
        bid_price_1 = mark_price - mark_price * aggression * factor/4
        bid_price_2 = mark_price - mark_price * aggression * factor/2
        bid_price_3 = mark_price - mark_price * aggression * factor
        ask_price_1 = mark_price + mark_price * aggression * factor/4
        ask_price_2 = mark_price + mark_price * aggression * factor/2
        ask_price_3 = mark_price + mark_price * aggression * factor
        Add above to determine_ask_price and determine_bid_price
        prices.append(above_prices)
        
        """
        # Determine the desired position size based on risk management rules
        #Logic here


        # Calculate the position size based on the risk per trade and the current price/volatility
        #Logic here
        return position_size




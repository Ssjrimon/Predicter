package com.example.predicter.data

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.google.gson.annotations.SerializedName

// UI Navigation tabs
enum class NavTab {
    WATCHLIST, SCANNER, SIZER, POSITIONS, SAVED, DETAIL
}

data class KalshiMarketsResponse(
    @SerializedName("markets") val markets: List<KalshiMarket>?,
    @SerializedName("cursor") val cursor: String? = null
)

data class KalshiCandlesticksResponse(
    @SerializedName("candlesticks") val candlesticks: List<KalshiCandlestick>?
)

data class KalshiCandlestick(
    @SerializedName("end_period_ts") val endPeriodTs: Long?,
    @SerializedName("open") val open: Double?,
    @SerializedName("high") val high: Double?,
    @SerializedName("low") val low: Double?,
    @SerializedName("close") val close: Double?,
    @SerializedName("volume") val volume: Long?,
    @SerializedName("open_interest") val openInterest: Long?
)

data class KalshiMarket(
    @SerializedName("ticker") val ticker: String?,
    @SerializedName("title") val title: String?,
    @SerializedName("status") val status: String?,
    @SerializedName("latest_quote_yes") val latestQuoteYes: Double? = null,
    @SerializedName("latest_quote_no") val latestQuoteNo: Double? = null,
    @SerializedName("yes_bid") val yesBid: Int? = null,
    @SerializedName("yes_ask") val yesAsk: Int? = null,
    @SerializedName("no_bid") val noBid: Int? = null,
    @SerializedName("no_ask") val noAsk: Int? = null,
    @SerializedName("last_price") val lastPrice: Int? = null,
    @SerializedName("expiration_time") val expirationTime: String? = null,
    @SerializedName("volume_24h") val volume24h: Long? = null,
    @SerializedName("open_interest") val openInterest: Long? = null,
    @SerializedName("last_updated") val lastUpdated: String? = null
)

data class KalshiPortfolioResponse(
    @SerializedName("positions") val positions: List<KalshiApiPosition>?
)

data class KalshiApiPosition(
    @SerializedName("ticker") val ticker: String?,
    @SerializedName("market_ticker") val marketTicker: String?,
    @SerializedName("position") val position: Int?,
    @SerializedName("realized_pnl") val realizedPnl: Long?,
    @SerializedName("rest_cost_basis") val restCostBasis: Long?
)

// Data models
data class TrendingMarket(

    val id: String,
    val name: String,
    val probability: Int,
    val expirationDate: String,
    val history: List<Float>
)

data class WatchlistOpportunity(
    val id: String,
    val title: String,
    val side: String,
    val price: Int,
    val yesPrice: Int,
    val noPrice: Int,
    val modelProb: Int,
    val multiplier: Double,
    val dataPoints: List<String>,
    val thesis: String,
    val sentimentScore: Int? = null,
    val volatilityScore: Double = 0.0,
    val history: List<Float> = emptyList()
)

data class KalshiOpportunity(
    val id: String,
    val eventTitle: String,
    val kalshiYes: Int,
    val kalshiNo: Int,
    val modelProbability: Int,
    val expectedValue: Int,
    val action: String,
    val timestamp: Long,
    val priceHistory: List<Float> = emptyList(),
    val volatilityHistory: List<Float> = emptyList(),
    val sentimentHistory: List<Float> = emptyList()
)

data class KalshiPosition(
    val id: String,
    val eventTitle: String,
    val side: String,
    val entryCost: Int,
    val currentCost: Int,
    val contractsActive: Int,
    val totalInvested: Int,
    val guaranteedPayout: Int,
    val status: String
)

// Room Entity for persistent bookmarks
@Entity(tableName = "saved_opportunities")
data class SavedOpportunity(
    @PrimaryKey val id: String,
    val eventTitle: String,
    val kalshiYes: Int,
    val kalshiNo: Int,
    val modelProbability: Int,
    val expectedValue: Int,
    val action: String,
    val timestamp: Long,
    val category: String
)

// UI State sealed class
sealed class EdgeState {
    object Initializing : EdgeState()
    object Offline : EdgeState()
    data class LiveData(
        val opportunities: List<KalshiOpportunity>,
        val lastUpdate: Long
    ) : EdgeState()
}

// Position Sizing calculator logic (Kelly Criterion helper)
class SizerCalculator {
    fun parsePrice(input: String): Double {
        return input.toDoubleOrNull() ?: 0.0
    }
    fun calculateMaxShares(capital: Double, pricePerShare: Double): Long {
        if (pricePerShare <= 0.0) return 0L
        return (capital / pricePerShare).toLong()
    }
}

package com.example.predicter.data

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.GET
import retrofit2.http.Query

interface KalshiApiService {
    @GET("trade-api/v2/markets")
    suspend fun getLiveMarkets(
        @Query("status") status: String = "open",
        @Query("limit") limit: Int = 100,
        @Query("cursor") cursor: String? = null
    ): KalshiMarketsResponse

    @GET("trade-api/v2/portfolio/positions")
    suspend fun getPortfolioPositions(): KalshiPortfolioResponse

    @GET("trade-api/v2/markets/{ticker}/candlesticks")
    suspend fun getMarketCandlesticks(
        @retrofit2.http.Path("ticker") ticker: String,
        @Query("period_interval") periodInterval: Int = 1440,
        @Query("limit") limit: Int = 20
    ): KalshiCandlesticksResponse
}

object AuthManager {
    var userToken: String? = null
}

object KalshiNetwork {
    private const val BASE_URL = "https://external-api.kalshi.com/"
    
    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }
    
    private val client = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .addInterceptor { chain ->
            val requestBuilder = chain.request().newBuilder()
                .header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                .header("Accept", "application/json")
                .header("Content-Type", "application/json")
            AuthManager.userToken?.let { token ->
                requestBuilder.header("Authorization", "Bearer $token")
            }
            chain.proceed(requestBuilder.build())
        }.build()

    val api: KalshiApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(KalshiApiService::class.java)
    }
}


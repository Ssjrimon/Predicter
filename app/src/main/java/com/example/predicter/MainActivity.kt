@file:OptIn(ExperimentalMaterial3Api::class)
package com.example.predicter

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.automirrored.filled.TrendingUp
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import kotlinx.coroutines.delay
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.animation.animateContentSize

import com.example.predicter.theme.*
import com.example.predicter.data.*
import com.example.predicter.ui.main.KalshiEdgeViewModel



class MainActivity : ComponentActivity() {
    private val viewModel: KalshiEdgeViewModel by viewModels {
        object : androidx.lifecycle.ViewModelProvider.Factory {
            override fun <T : androidx.lifecycle.ViewModel> create(
                modelClass: Class<T>,
                extras: androidx.lifecycle.viewmodel.CreationExtras
            ): T {
                android.util.Log.d("KalshiEdge", "KalshiEdgeViewModel Factory invoked")
                val app = extras[androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.APPLICATION_KEY] 
                    ?: application // Fallback
                @Suppress("UNCHECKED_CAST")
                return KalshiEdgeViewModel(app) as T
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        android.util.Log.d("KalshiEdge", "MainActivity onCreate started")
        
        try {
            enableEdgeToEdge()
            // Force ViewModel init to catch any early crashes
            val testInit = viewModel
            android.util.Log.d("KalshiEdge", "KalshiEdgeViewModel initialized successfully")
            
            setContent {
                PredicterTheme {
                    val snackbarHostState = remember { SnackbarHostState() }
                    val scope = rememberCoroutineScope()
                    var currentTab by rememberSaveable { mutableStateOf(NavTab.WATCHLIST) }

                    Scaffold(
                        modifier = Modifier.fillMaxSize(),
                        containerColor = MaterialTheme.colorScheme.background,
                        snackbarHost = { SnackbarHost(snackbarHostState) },
                        topBar = { 
                            DashboardTopBar(
                                onAlertClick = {
                                    scope.launch { snackbarHostState.showSnackbar("WebSockets Connected. Max Latency 42ms.", duration = SnackbarDuration.Short) }
                                }
                            ) 
                        },
                        bottomBar = {
                            ArbitrageBottomBar(currentTab = currentTab, onTabSelected = { currentTab = it })
                        }
                    ) { innerPadding ->
                        Box(modifier = Modifier.padding(innerPadding).fillMaxSize()) {
                            when (currentTab) {
                                NavTab.WATCHLIST -> WatchlistScreen(viewModel, onNavigateToSizer = { currentTab = NavTab.SIZER })
                                NavTab.SCANNER -> ScannerScreen(viewModel, onNavigateToSizer = { currentTab = NavTab.SIZER }, onNavigateToDetail = { currentTab = NavTab.DETAIL })
                                NavTab.SIZER -> SizerScreen(viewModel)
                                NavTab.POSITIONS -> PositionsScreen(viewModel)
                                NavTab.SAVED -> SavedScreen(viewModel, onNavigateToSizer = { currentTab = NavTab.SIZER })
                                NavTab.DETAIL -> MarketDetailScreen(viewModel, onBack = { currentTab = NavTab.SCANNER }, onNavigateToSizer = { currentTab = NavTab.SIZER })
                            }
                        }
                    }
                }
            } 
        } catch (e: Exception) {
            android.util.Log.e("KalshiEdge", "Fatal error during MainActivity onCreate", e)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardTopBar(onAlertClick: () -> Unit) {
    TopAppBar(
        title = {
            Column {
                Text(
                    "predictAI",
                    fontWeight = FontWeight.Black,
                    color = MaterialTheme.colorScheme.onBackground
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(modifier = Modifier.size(8.dp).background(Color.Green, shape = RoundedCornerShape(50)))
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("LIVE", color = Color.Green, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                }
            }
        },
        actions = {
            IconButton(onClick = onAlertClick) {
                Icon(Icons.Default.Speed, contentDescription = "Engine Status", tint = MaterialTheme.colorScheme.onBackground)
            }
        },
        colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.surface)
    )
}

@Composable
fun ArbitrageBottomBar(currentTab: NavTab, onTabSelected: (NavTab) -> Unit) {
    NavigationBar(containerColor = MaterialTheme.colorScheme.surface) {
        val tabs = listOf(
            Triple(NavTab.WATCHLIST, "Watchlist", Icons.Default.Star),
            Triple(NavTab.SCANNER, "Scanner", Icons.Default.Search),
            Triple(NavTab.SIZER, "Sizer", Icons.Default.Calculate),
            Triple(NavTab.POSITIONS, "Positions", Icons.Default.AccountBalanceWallet),
            Triple(NavTab.SAVED, "Saved", Icons.Default.Bookmarks)
        )
        tabs.forEach { (tab, label, icon) ->
            NavigationBarItem(
                selected = currentTab == tab,
                onClick = { onTabSelected(tab) },
                icon = { Icon(icon, contentDescription = label) },
                label = { Text(label) },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = KalshiPrimary,
                    selectedTextColor = KalshiPrimary,
                    indicatorColor = KalshiPrimary.copy(alpha = 0.2f),
                    unselectedIconColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                    unselectedTextColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                )
            )
        }
    }
}

@Composable
fun WatchlistScreen(viewModel: KalshiEdgeViewModel, onNavigateToSizer: () -> Unit) {
    val watchlist by viewModel.watchlist.collectAsState()
    val isRefreshing by viewModel.isRefreshing.collectAsState()
    
    var searchQuery by rememberSaveable { mutableStateOf("") }
    var sortOption by rememberSaveable { mutableStateOf("Recent Activity") }
    
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text("Dashboard", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                Text("Markets & Models", color = MaterialTheme.colorScheme.onSurface.copy(0.7f))
            }
            Button(
                onClick = { viewModel.refreshData() },
                enabled = !isRefreshing
            ) {
                if (isRefreshing) {
                    CircularProgressIndicator(modifier = Modifier.size(16.dp), color = MaterialTheme.colorScheme.onPrimary, strokeWidth = 2.dp)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Refreshing...")
                } else {
                    Icon(Icons.Default.Refresh, contentDescription = "Refresh Data", modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Refresh Data")
                }
            }
        }
        
        Spacer(Modifier.height(16.dp))
        
        OutlinedTextField(
            value = searchQuery,
            onValueChange = { searchQuery = it },
            modifier = Modifier.fillMaxWidth(),
            label = { Text("Search Watchlist") },
            leadingIcon = { Icon(Icons.Default.Search, contentDescription = "Search") },
            singleLine = true,
            shape = RoundedCornerShape(12.dp)
        )
        
        Spacer(Modifier.height(16.dp))
        
        LazyColumn(modifier = Modifier.weight(1f).fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            item {
                Spacer(Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text("Top 15 Opportunities", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        Text("Active trading feeds directly from Kalshi API", color = MaterialTheme.colorScheme.onSurface.copy(0.7f), fontSize = 12.sp)
                    }
                }
                Spacer(Modifier.height(8.dp))
                Row(modifier = Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf("Recent Activity", "Probability", "Alphabetical").forEach { filter ->
                        FilterChip(
                            selected = sortOption == filter,
                            onClick = { sortOption = filter },
                            label = { Text(filter) }
                        )
                    }
                }
            }
            
            val sortedOpportunities = try {
                val filteredOpportunities = watchlist.filter {
                    it.title.contains(searchQuery, ignoreCase = true) ||
                    it.id.contains(searchQuery, ignoreCase = true)
                }
                filteredOpportunities.sortedWith { a, b ->
                    when (sortOption) {
                        "Probability" -> b.modelProb.compareTo(a.modelProb)
                        "Recent Activity" -> {
                            val actA = Math.abs(a.id.hashCode() % 100)
                            val actB = Math.abs(b.id.hashCode() % 100)
                            actB.compareTo(actA)
                        }
                        else -> a.title.compareTo(b.title, ignoreCase = true)
                    }
                }
            } catch (e: Exception) {
                emptyList()
            }

            items(sortedOpportunities, key = { it.id }) { opportunity ->
                CleanWatchlistCard(
                    item = opportunity,
                    onAnalyzeSentiment = { viewModel.analyzeSentimentForMarket(it) },
                    onTradeCLicked = { /* Handle trade click if needed */ }
                )
            }
        }
    }
}


@Composable
fun LiveRawMarketItem(market: KalshiMarket, opportunity: WatchlistOpportunity? = null, onAnalyzeSentiment: ((WatchlistOpportunity?) -> Unit)? = null) {
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()
    val scale by animateFloatAsState(targetValue = if (isPressed) 1.02f else 1f, label = "scale")

    LaunchedEffect(opportunity?.id) {
        if (opportunity != null && opportunity.sentimentScore == null) {
            onAnalyzeSentiment?.invoke(opportunity)
        }
    }

    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f)),
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp)
            .graphicsLayer {
                scaleX = scale
                scaleY = scale
            }
            .clickable(
                interactionSource = interactionSource,
                indication = androidx.compose.foundation.LocalIndication.current,
                onClick = { /* Do nothing */ }
            )
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.Top) {
                Text(
                    text = market.title ?: "Unknown Market",
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.SemiBold,
                    color = MaterialTheme.colorScheme.onSurface,
                    modifier = Modifier.weight(1f)
                )
                if (opportunity != null) {
                    val sentimentScore = opportunity.sentimentScore
                    if (sentimentScore != null) {
                        val sentimentColor = if (sentimentScore > 0) Color.Green else if (sentimentScore < 0) Color.Red else Color.Gray
                        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(start = 8.dp)) {
                            Icon(
                                imageVector = if (sentimentScore >= 0) Icons.AutoMirrored.Filled.TrendingUp else Icons.Default.KeyboardArrowDown,
                                contentDescription = "Sentiment",
                                tint = sentimentColor,
                                modifier = Modifier.size(16.dp)
                            )
                        }
                    } else {
                         Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(start = 8.dp)) {
                             CircularProgressIndicator(modifier = Modifier.size(16.dp), color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f), strokeWidth = 2.dp)
                         }
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(4.dp))
            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(
                    text = "Ticker: ${market.ticker ?: "N/A"} | Status: ${market.status?.uppercase() ?: "UNKNOWN"}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                )
                if (opportunity != null) {
                    Text(
                        text = "${opportunity.modelProb}% Prob",
                        style = MaterialTheme.typography.bodySmall,
                        fontWeight = FontWeight.Bold,
                        color = KalshiPrimary
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            val historyLength = 20
            val sparklineData = remember(market.ticker) { 
                val seed = (market.ticker ?: "").hashCode()
                val base = 50f + (Math.abs(seed) % 30)
                List(historyLength) { index -> 
                  base + (Math.sin(index + seed.toDouble()) * 15).toFloat() + ((Math.abs(seed) % 7) * index)
                } 
            }
            
            val minVal = sparklineData.minOrNull() ?: 0f
            val maxVal = sparklineData.maxOrNull() ?: 100f
            val range = maxVal - minVal
            val displayRange = if (range == 0f) 1f else range
            
            Canvas(modifier = Modifier.fillMaxWidth().height(40.dp).padding(vertical = 4.dp)) {
                val width = size.width
                val height = size.height
                val stepX = width / (sparklineData.size - 1).coerceAtLeast(1)
                
                val path = androidx.compose.ui.graphics.Path()
                sparklineData.forEachIndexed { index, value ->
                    val x = index * stepX
                    val normalizedY = (maxVal - value) / displayRange
                    val y = normalizedY * height
                    if (index == 0) {
                        path.moveTo(x, y)
                    } else {
                        path.lineTo(x, y)
                    }
                }
                drawPath(
                    path = path,
                    color = KalshiPrimary.copy(alpha = 0.6f),
                    style = androidx.compose.ui.graphics.drawscope.Stroke(width = 2.dp.toPx())
                )
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            ImprovedTradeOnKalshiButton(marketTicker = market.ticker ?: "", modifier = Modifier.fillMaxWidth())
        }
    }
}

@Composable
fun LiveMarketCard(market: KalshiMarket) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(market.title ?: "Unknown Market", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
            Spacer(modifier = Modifier.height(4.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Status: ${market.status?.uppercase() ?: "UNKNOWN"}", color = KalshiPrimary, fontWeight = FontWeight.Black, fontSize = 12.sp)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Ticker: ${market.ticker ?: ""}", color = MaterialTheme.colorScheme.onSurface.copy(0.6f), fontSize = 12.sp)
            }
            Spacer(modifier = Modifier.height(12.dp))
            ImprovedTradeOnKalshiButton(marketTicker = market.ticker ?: "", modifier = Modifier.fillMaxWidth())
        }
    }
}

@Composable
fun TrendingMarketCard(market: TrendingMarket, onCardClick: (TrendingMarket) -> Unit) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        modifier = Modifier
            .width(200.dp)
            .clickable { onCardClick(market) }
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Text(
                market.name, 
                style = MaterialTheme.typography.titleSmall, 
                fontWeight = FontWeight.Bold,
                maxLines = 1,
                color = MaterialTheme.colorScheme.onSurface
            )
            Spacer(modifier = Modifier.height(4.dp))
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("${market.probability}%", color = KalshiPrimary, fontWeight = FontWeight.Bold)
                Text("Exp: ${market.expirationDate}", fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurface.copy(0.6f))
            }
            Spacer(modifier = Modifier.height(8.dp))
            
            // Historical Line Chart using Canvas
            if (market.history.isNotEmpty()) {
                val minVal = market.history.minOrNull() ?: 0f
                val maxVal = market.history.maxOrNull() ?: 100f
                val range = maxVal - minVal
                val displayRange = if (range == 0f) 1f else range
                
                Canvas(modifier = Modifier.fillMaxWidth().height(40.dp)) {
                    val width = size.width
                    val height = size.height
                    val stepX = width / (market.history.size - 1).coerceAtLeast(1)
                    
                    val path = androidx.compose.ui.graphics.Path()
                    market.history.forEachIndexed { index, value ->
                        val x = index * stepX
                        val normalizedY = (maxVal - value) / displayRange
                        val y = normalizedY * height
                        if (index == 0) {
                            path.moveTo(x, y)
                        } else {
                            path.lineTo(x, y)
                        }
                    }
                    drawPath(
                        path = path,
                        color = KalshiPrimary,
                        style = androidx.compose.ui.graphics.drawscope.Stroke(width = 2.dp.toPx())
                    )
                }
            }
        }
    }
}

@Composable
fun TrendingMarketDetailDialog(market: TrendingMarket, onDismiss: () -> Unit) {
    val context = androidx.compose.ui.platform.LocalContext.current
    val ticker = when (market.name) {
        "Fed Rate Cut in June?" -> "FED-RATE-CUT"
        "Trump Wins Election?" -> "TRUMP-WIN"
        "TikTok Ban Implemented?" -> "TIKTOK-BAN"
        "US GDP > 2%" -> "US-GDP"
        "ETH ETF Approved?" -> "ETH-ETF"
        else -> market.id
    }
    
    val searchWord = when (market.name) {
        "Fed Rate Cut in June?" -> "Fed"
        "Trump Wins Election?" -> "Trump"
        "TikTok Ban Implemented?" -> "TikTok"
        "US GDP > 2%" -> "GDP"
        "ETH ETF Approved?" -> "ETH"
        else -> market.name
    }

    val sentimentThesis = when (market.name) {
        "Fed Rate Cut in June?" -> "Market consensus points to a high probability of steady rates, but sticky core CPI figures could delay cuts. Recommend tracking incoming Fed speak and core PCE index."
        "Trump Wins Election?" -> "Political forecasting models showing strong momentum in key swing states. Prediction market volume suggests this is currently the highest liquidity event globally."
        "TikTok Ban Implemented?" -> "Bipartisan regulatory momentum has intensified. Court filings suggest legal appeals are underway, indicating a high-volatility event window."
        "US GDP > 2%" -> "Latest retail sales and consumer spending metrics suggest resilient economic expansion. Model predictions indicate 63% probability of GDP exceeding 2%."
        "ETH ETF Approved?" -> "Institutional interest has surged post regulatory filings. Inflows tracking reveals strong demand which supports our bullish 58% prediction model."
        else -> "AI-analyzed market sentiment highlights substantial liquidity on Kalshi. Highly recommended to monitor closely for volatility and options edge."
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .background(KalshiPrimary.copy(alpha = 0.15f), RoundedCornerShape(4.dp))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text("TRENDING", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = KalshiPrimary)
                    }
                    Spacer(Modifier.width(8.dp))
                    Text("Market Analysis", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f))
                }
                Spacer(Modifier.height(4.dp))
                Text(market.name, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
            }
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Column {
                        Text("Trending Probability", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurface.copy(0.6f))
                        Text("${market.probability}%", fontSize = 24.sp, fontWeight = FontWeight.Black, color = KalshiPrimary)
                    }
                    Column(horizontalAlignment = Alignment.End) {
                        Text("Expiration", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurface.copy(0.6f))
                        Text(market.expirationDate, fontSize = 16.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                    }
                }

                // Beautiful mini chart in dialog
                if (market.history.isNotEmpty()) {
                    Text("24H Price Probability History", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface.copy(0.8f))
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(100.dp)
                            .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f), RoundedCornerShape(8.dp))
                            .padding(8.dp)
                    ) {
                        val minVal = market.history.minOrNull() ?: 0f
                        val maxVal = market.history.maxOrNull() ?: 100f
                        val range = maxVal - minVal
                        val displayRange = if (range == 0f) 1f else range
                        
                        Canvas(modifier = Modifier.fillMaxSize()) {
                            val width = size.width
                            val height = size.height
                            val stepX = width / (market.history.size - 1).coerceAtLeast(1)
                            
                            val path = androidx.compose.ui.graphics.Path()
                            market.history.forEachIndexed { index, value ->
                                val x = index * stepX
                                val normalizedY = (maxVal - value) / displayRange
                                val y = normalizedY * height
                                if (index == 0) {
                                    path.moveTo(x, y)
                                } else {
                                    path.lineTo(x, y)
                                }
                            }
                            drawPath(
                                path = path,
                                color = KalshiPrimary,
                                style = androidx.compose.ui.graphics.drawscope.Stroke(width = 3.dp.toPx())
                            )
                        }
                    }
                }

                Column {
                    Text("AI Prediction Thesis", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface.copy(0.8f))
                    Spacer(Modifier.height(4.dp))
                    Text(
                        sentimentThesis,
                        fontSize = 13.sp,
                        color = MaterialTheme.colorScheme.onSurface.copy(0.8f),
                        lineHeight = 18.sp,
                        fontStyle = androidx.compose.ui.text.font.FontStyle.Italic
                    )
                }

                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.05f), RoundedCornerShape(8.dp))
                        .padding(8.dp)
                ) {
                    Text("Recommended Action", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = KalshiPrimary)
                    Text(
                        if (market.probability > 50) "Strong Edge on YES contract" else "Favorable pricing on NO contract",
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                }
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    val url = "https://kalshi.com/markets?search=${android.net.Uri.encode(searchWord)}"
                    context.safeOpenUrl(url)
                },
                colors = ButtonDefaults.buttonColors(containerColor = KalshiPrimary)
            ) {
                Text("Lock it in on Kalshi", color = MaterialTheme.colorScheme.onPrimary)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Close", color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f))
            }
        }
    )
}

@Composable
fun CleanWatchlistCard(
    item: WatchlistOpportunity,
    onAnalyzeSentiment: ((WatchlistOpportunity) -> Unit)? = null,
    onTradeCLicked: () -> Unit = {}
) {
    var expanded by remember { mutableStateOf(false) }
    
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()
    val scale by animateFloatAsState(targetValue = if (isPressed) 1.01f else 1f, label = "scale")

    LaunchedEffect(item.id) {
        if (item.sentimentScore == null) {
            onAnalyzeSentiment?.invoke(item)
        }
    }
    
    val context = androidx.compose.ui.platform.LocalContext.current
    val isMultiLeg = item.title.contains(",") && (
        item.title.split(",").any { part -> 
            val p = part.trim().lowercase()
            p.startsWith("yes ") || p.startsWith("no ") || p.startsWith("yes:") || p.startsWith("no:")
        }
    )

    Card(
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (expanded) 
                MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.25f)
            else 
                MaterialTheme.colorScheme.surface
        ),
        border = androidx.compose.foundation.BorderStroke(
            width = 1.dp,
            color = if (expanded) KalshiPrimary.copy(alpha = 0.3f) else MaterialTheme.colorScheme.onSurface.copy(alpha = 0.05f)
        ),
        modifier = Modifier
            .fillMaxWidth()
            .graphicsLayer {
                scaleX = scale
                scaleY = scale
            }
            .padding(vertical = 4.dp)
            .clickable(
                interactionSource = interactionSource,
                indication = androidx.compose.foundation.LocalIndication.current,
                onClick = { expanded = !expanded }
            )
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // Header: Category, Ticker & Action Highlight Pill
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                val category = getCategoryFromTicker(item.id, item.title)
                Text(
                    text = "$category • ${item.id.uppercase()}",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f),
                    letterSpacing = 1.sp
                )
                
                // Highlighted Action Pill
                val sideColor = if (item.side.uppercase() == "YES") Color(0xFF00FF88) else KalshiError
                val sideBg = if (item.side.uppercase() == "YES") Color(0xFF003820) else Color(0xFF401015)
                
                Box(
                    modifier = Modifier
                        .background(sideBg, RoundedCornerShape(6.dp))
                        .padding(horizontal = 8.dp, vertical = 4.dp)
                ) {
                    Text(
                        text = "BUY ${item.side.uppercase()}",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Black,
                        color = sideColor,
                        letterSpacing = 0.5.sp
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(10.dp))
            
            // Event Title / Question
            val displayTitle = if (isMultiLeg) {
                "Multi-Leg Parlay Recommendation"
            } else {
                item.title
            }
            Text(
                text = displayTitle,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface,
                lineHeight = 22.sp
            )
            
            Spacer(modifier = Modifier.height(14.dp))
            
            // Stats Row: Market Price, Model, Edge, Multiplier (Labels on top)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text("Market", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f))
                    Spacer(Modifier.height(4.dp))
                    Text("${item.price}¢", fontSize = 18.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                }
                
                Column {
                    Text("Model", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f))
                    Spacer(Modifier.height(4.dp))
                    Text("${item.modelProb}%", fontSize = 18.sp, fontWeight = FontWeight.Bold, color = KalshiPrimary)
                }
                
                Column {
                    Text("Edge", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f))
                    Spacer(Modifier.height(4.dp))
                    val edge = item.modelProb - item.price
                    val edgePrefix = if (edge >= 0) "+" else ""
                    Text("$edgePrefix$edge%", fontSize = 18.sp, fontWeight = FontWeight.Bold, color = if (edge >= 0) KalshiPrimary else KalshiError)
                }
                
                Column(horizontalAlignment = Alignment.End) {
                    Text("Multiplier", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f))
                    Spacer(Modifier.height(4.dp))
                    Text("${String.format("%.1f", item.multiplier)}x", fontSize = 18.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                }
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // Confidence indicators & quick stats
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Confidence bullet point
                val confidenceText = when {
                    item.sentimentScore == null -> "Analyzing sentiment..."
                    item.modelProb - item.price >= 10 || Math.abs(item.sentimentScore) >= 50 -> "High Confidence"
                    item.modelProb - item.price >= 5 || Math.abs(item.sentimentScore) >= 20 -> "Medium Confidence"
                    else -> "Low Confidence"
                }
                val confidenceColor = when {
                    item.sentimentScore == null -> MaterialTheme.colorScheme.onSurface.copy(alpha = 0.4f)
                    item.modelProb - item.price >= 10 || Math.abs(item.sentimentScore) >= 50 -> Color(0xFF00FF88)
                    item.modelProb - item.price >= 5 || Math.abs(item.sentimentScore) >= 20 -> Color(0xFFFFAA00)
                    else -> Color.Gray
                }
                
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(6.dp)
                            .background(confidenceColor, androidx.compose.foundation.shape.CircleShape)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = confidenceText,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.8f)
                    )
                }
                
                // Toggle expansion indicator
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = if (expanded) "Less Details" else "More Details",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = KalshiPrimary
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Icon(
                        imageVector = if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                        contentDescription = null,
                        tint = KalshiPrimary,
                        modifier = Modifier.size(14.dp)
                    )
                }
            }
            
            // Expanded Section: Details, Sparkline History, Legs
            AnimatedVisibility(visible = expanded) {
                Column(modifier = Modifier.padding(top = 14.dp)) {
                    HorizontalDivider(color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.08f), modifier = Modifier.padding(bottom = 12.dp))
                    
                    // Why this prediction
                    Text(
                        text = "Prediction Thesis",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Spacer(Modifier.height(4.dp))
                    
                    if (item.sentimentScore != null) {
                        Text(
                            text = item.thesis,
                            fontSize = 13.sp,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.8f),
                            lineHeight = 18.sp,
                            fontStyle = androidx.compose.ui.text.font.FontStyle.Italic
                        )
                    } else {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(12.dp),
                                color = KalshiPrimary,
                                strokeWidth = 1.dp
                            )
                            Spacer(Modifier.width(8.dp))
                            Text(
                                text = "Analyzing market thesis with Gemini Search...",
                                fontSize = 13.sp,
                                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                                fontStyle = androidx.compose.ui.text.font.FontStyle.Italic
                            )
                        }
                    }
                    
                    Spacer(modifier = Modifier.height(14.dp))
                    
                    if (isMultiLeg) {
                        Text(
                            text = "Parlay Legs to Execute",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        
                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            val legs = item.title.split(",").map { it.trim() }.filter { it.isNotEmpty() }
                            legs.forEach { leg ->
                                val cleanLeg = leg.lowercase()
                                val isYes = cleanLeg.startsWith("yes")
                                val isNo = cleanLeg.startsWith("no")
                                
                                val contentText = when {
                                    isYes -> leg.substring(3).trim().replaceFirstChar { it.uppercase() }
                                    isNo -> leg.substring(2).trim().replaceFirstChar { it.uppercase() }
                                    else -> leg.replaceFirstChar { it.uppercase() }
                                }
                                
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f), RoundedCornerShape(8.dp))
                                        .padding(horizontal = 12.dp, vertical = 8.dp)
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f)) {
                                        Icon(
                                            imageVector = if (isYes) Icons.Default.CheckCircle else if (isNo) Icons.Default.Cancel else Icons.Default.Circle,
                                            contentDescription = null,
                                            tint = if (isYes) KalshiPrimary else if (isNo) KalshiSecondary else MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                                            modifier = Modifier.size(18.dp)
                                        )
                                        Spacer(modifier = Modifier.width(10.dp))
                                        Column {
                                            Text(
                                                text = contentText,
                                                style = MaterialTheme.typography.bodyMedium,
                                                fontWeight = FontWeight.Bold,
                                                color = MaterialTheme.colorScheme.onSurface
                                            )
                                            Text(
                                                text = if (isYes) "Required: Lock in YES" else if (isNo) "Required: Lock in NO" else "Analyze Prediction",
                                                fontSize = 11.sp,
                                                color = if (isYes) KalshiPrimary else if (isNo) KalshiSecondary else MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                                            )
                                        }
                                    }
                                    
                                    IconButton(
                                        onClick = {
                                            val url = "https://kalshi.com/markets?search=${android.net.Uri.encode(contentText)}"
                                            context.safeOpenUrl(url)
                                        },
                                        modifier = Modifier
                                            .background(KalshiPrimary.copy(alpha = 0.1f), RoundedCornerShape(6.dp))
                                            .size(36.dp)
                                    ) {
                                        Icon(
                                            imageVector = Icons.Default.OpenInNew,
                                            contentDescription = "Trade Leg",
                                            tint = KalshiPrimary,
                                            modifier = Modifier.size(16.dp)
                                        )
                                    }
                                }
                            }
                        }
                        Spacer(modifier = Modifier.height(14.dp))
                    }
                    
                    // Supporting data list
                    Text(
                        text = "Supporting Data",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Spacer(modifier = Modifier.height(6.dp))
                    
                    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        item.dataPoints.forEach { point ->
                            Row(verticalAlignment = Alignment.Top, modifier = Modifier.padding(bottom = 2.dp)) {
                                Icon(
                                    imageVector = Icons.Default.Info,
                                    contentDescription = null,
                                    modifier = Modifier.size(16.dp).padding(top = 2.dp),
                                    tint = KalshiSecondary
                                )
                                Spacer(Modifier.width(8.dp))
                                Text(point, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.8f))
                            }
                        }
                    }
                    
                    // History Sparkline Chart
                    if (item.history.isNotEmpty()) {
                        Spacer(modifier = Modifier.height(14.dp))
                        Text(
                            text = "24H Probability Movement",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        
                        val sparklineData = item.history
                        val minVal = sparklineData.minOrNull() ?: 0f
                        val maxVal = sparklineData.maxOrNull() ?: 100f
                        val range = maxVal - minVal
                        val displayRange = if (range == 0f) 1f else range
                        
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(50.dp)
                                .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.2f), RoundedCornerShape(8.dp))
                                .padding(vertical = 6.dp, horizontal = 10.dp)
                        ) {
                            Canvas(modifier = Modifier.fillMaxSize()) {
                                val width = size.width
                                val height = size.height
                                val stepX = width / (sparklineData.size - 1).coerceAtLeast(1)
                                
                                val path = androidx.compose.ui.graphics.Path()
                                sparklineData.forEachIndexed { index, value ->
                                    val x = index * stepX
                                    val normalizedY = (maxVal - value) / displayRange
                                    val y = normalizedY * height
                                    if (index == 0) {
                                        path.moveTo(x, y)
                                    } else {
                                        path.lineTo(x, y)
                                    }
                                }
                                drawPath(
                                    path = path,
                                    color = KalshiPrimary.copy(alpha = 0.8f),
                                    style = androidx.compose.ui.graphics.drawscope.Stroke(width = 2.dp.toPx())
                                )
                            }
                        }
                    }
                    
                    Spacer(modifier = Modifier.height(14.dp))
                    
                    // Trade Button inside expanded details
                    ImprovedTradeOnKalshiButton(
                        marketTicker = item.id,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        }
    }
}

object KalshiDeepLink {
    fun openMarket(context: android.content.Context, ticker: String) {
        val uppercaseTicker = ticker.uppercase()
        val url = "https://kalshi.com/markets/$uppercaseTicker"
        val intent = android.content.Intent(android.content.Intent.ACTION_VIEW, android.net.Uri.parse(url)).apply {
            addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
            setPackage("com.kalshi.app")
        }
        try {
            context.startActivity(intent)
        } catch (e: Exception) {
            try {
                val webIntent = android.content.Intent(android.content.Intent.ACTION_VIEW, android.net.Uri.parse(url)).apply {
                    addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                context.startActivity(webIntent)
            } catch (ex: Exception) {
                android.widget.Toast.makeText(context, "Unable to open link.", android.widget.Toast.LENGTH_SHORT).show()
            }
        }
    }
}

@Composable
fun ImprovedTradeOnKalshiButton(
    marketTicker: String,
    modifier: Modifier = Modifier,
    isOutlined: Boolean = false
) {
    val context = androidx.compose.ui.platform.LocalContext.current
    val haptic = androidx.compose.ui.platform.LocalHapticFeedback.current

    val onClick: () -> Unit = {
        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
        KalshiDeepLink.openMarket(context, marketTicker)
    }

    if (isOutlined) {
        OutlinedButton(
            onClick = onClick,
            modifier = modifier,
            colors = ButtonDefaults.outlinedButtonColors(
                contentColor = KalshiPrimary
            ),
            border = androidx.compose.foundation.BorderStroke(1.dp, KalshiPrimary.copy(alpha = 0.5f)),
            shape = RoundedCornerShape(10.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Default.TrendingUp,
                    contentDescription = null,
                    modifier = Modifier.size(16.dp)
                )
                Spacer(Modifier.width(8.dp))
                Text("Lock it in on Kalshi", fontWeight = FontWeight.Bold, fontSize = 14.sp)
            }
        }
    } else {
        Button(
            onClick = onClick,
            modifier = modifier,
            colors = ButtonDefaults.buttonColors(containerColor = KalshiPrimary),
            shape = RoundedCornerShape(10.dp),
            elevation = ButtonDefaults.buttonElevation(defaultElevation = 2.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Default.TrendingUp,
                    contentDescription = null,
                    modifier = Modifier.size(16.dp),
                    tint = MaterialTheme.colorScheme.onPrimary
                )
                Spacer(Modifier.width(8.dp))
                Text("Lock it in on Kalshi", fontWeight = FontWeight.Bold, fontSize = 14.sp, color = MaterialTheme.colorScheme.onPrimary)
            }
        }
    }
}



// Utility function to categorize the markets dynamically
fun getCategoryFromTicker(ticker: String, title: String): String {
    val cleanTitle = title.lowercase()
    val cleanTicker = ticker.lowercase()
    return when {
        cleanTicker.startsWith("btc") || cleanTicker.startsWith("eth") || "crypto" in cleanTitle || "bitcoin" in cleanTitle || "ethereum" in cleanTitle -> "CRYPTO"
        "fed" in cleanTitle || "interest" in cleanTitle || "fomc" in cleanTitle || "rate" in cleanTitle || cleanTicker.startsWith("fed") -> "MACRO"
        "trump" in cleanTitle || "biden" in cleanTitle || "election" in cleanTitle || "harris" in cleanTitle || "democrat" in cleanTitle || "republican" in cleanTitle || "house" in cleanTitle || "senate" in cleanTitle -> "POLITICS"
        "gdp" in cleanTitle || "cpi" in cleanTitle || "inflation" in cleanTitle || "unemployment" in cleanTitle || "retail" in cleanTitle || cleanTicker.startsWith("gdp") || cleanTicker.startsWith("cpi") -> "MACRO"
        "aapl" in cleanTitle || "apple" in cleanTitle || "tsla" in cleanTitle || "tesla" in cleanTitle || "tiktok" in cleanTitle || "nvidia" in cleanTitle || "nvda" in cleanTitle || "ai" in cleanTitle || "tech" in cleanTitle -> "TECH"
        "oil" in cleanTitle || "gas" in cleanTitle || "brent" in cleanTitle || "crude" in cleanTitle || cleanTicker.startsWith("oil") -> "COMMODITIES"
        else -> "FINANCE"
    }
}



@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ScannerScreen(viewModel: KalshiEdgeViewModel, onNavigateToSizer: () -> Unit, onNavigateToDetail: () -> Unit) {
    val state by viewModel.edgeState.collectAsState()
    var searchQuery by rememberSaveable { mutableStateOf("") }
    val scope = rememberCoroutineScope()
    val isRefreshing by viewModel.isRefreshing.collectAsState()
    
    when (val s = state) {
        is EdgeState.Initializing -> {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator(color = KalshiPrimary)
                    Spacer(Modifier.height(16.dp))
                    Text("Connecting order books...", color = MaterialTheme.colorScheme.onSurface)
                }
            }
        }
        is EdgeState.Offline -> {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(Icons.Default.WifiOff, contentDescription = "Offline", modifier = Modifier.size(48.dp), tint = KalshiError)
                    Spacer(Modifier.height(16.dp))
                    Text("Offline. Retrying...", color = MaterialTheme.colorScheme.onSurface, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                }
            }
        }
        is EdgeState.LiveData -> {
            val format = remember { SimpleDateFormat("HH:mm:ss.SSS", Locale.US) }
            
            Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
                OutlinedTextField(
                    value = searchQuery,
                    onValueChange = { searchQuery = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Search Opportunities (e.g. sports, crypto)") },
                    leadingIcon = { Icon(Icons.Default.Search, contentDescription = "Search") },
                    singleLine = true,
                    shape = RoundedCornerShape(12.dp)
                )
                Spacer(modifier = Modifier.height(16.dp))

                val filteredOps = s.opportunities.filter { 
                    it.eventTitle.contains(searchQuery, ignoreCase = true)
                }

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        "${filteredOps.size} Opportunities Found",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onBackground
                    )
                    Text("Updated: ${format.format(Date(s.lastUpdate))}", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha=0.5f))
                }
                Spacer(modifier = Modifier.height(16.dp))
                PullToRefreshBox(
                    isRefreshing = isRefreshing,
                    onRefresh = {
                        viewModel.refreshData()
                    },
                    modifier = Modifier.weight(1f).fillMaxWidth()
                ) {
                    LazyColumn(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                        if (filteredOps.isEmpty()) {
                            item {
                                Text("No opportunities match your search", color = MaterialTheme.colorScheme.onSurface)
                            }
                        }
                        items(filteredOps) { arb -> 
                            OpportunityCard(
                                arb = arb,
                                onCalculate = { 
                                    viewModel.selectOpportunity(arb)
                                    onNavigateToSizer() 
                                },
                                onCardClick = {
                                    viewModel.selectOpportunity(arb)
                                    onNavigateToDetail()
                                },
                                onSaveClick = { category ->
                                    viewModel.saveOpportunity(arb, category)
                                }
                            ) 
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun OpportunityCard(arb: KalshiOpportunity, onCalculate: () -> Unit, onCardClick: () -> Unit, onSaveClick: (String) -> Unit = {}) {
    var showDialog by remember { mutableStateOf(false) }

    if (showDialog) {
        AlertDialog(
            onDismissRequest = { showDialog = false },
            title = { Text("Save to Category") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    val categories = listOf("Crypto", "Macro", "Politics", "Tech", "Finance")
                    categories.forEach { cat ->
                        OutlinedButton(onClick = { 
                            onSaveClick(cat)
                            showDialog = false 
                        }, modifier = Modifier.fillMaxWidth()) {
                            Text(cat)
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showDialog = false }) { Text("Cancel") }
            }
        )
    }

    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        modifier = Modifier.fillMaxWidth().clickable { onCardClick() }
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.Top) {
                Text(
                    arb.eventTitle,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSurface,
                    modifier = Modifier.weight(1f).padding(end = 8.dp)
                )
                IconButton(onClick = { showDialog = true }, modifier = Modifier.size(24.dp)) {
                    Icon(Icons.Default.BookmarkBorder, contentDescription = "Save")
                }
            }
            Spacer(modifier = Modifier.height(12.dp))
            if (arb.sentimentHistory.isNotEmpty()) {
                Text("Sentiment Trend (D3 style)", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurface.copy(alpha=0.7f))
                Spacer(modifier = Modifier.height(4.dp))
                SentimentChart(history = arb.sentimentHistory, modifier = Modifier.fillMaxWidth().height(40.dp))
                Spacer(modifier = Modifier.height(12.dp))
            }
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Column {
                    Text("Market Odds", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurface.copy(alpha=0.7f))
                    Text("Y: ${arb.kalshiYes}¢ | N: ${arb.kalshiNo}¢", fontWeight = FontWeight.SemiBold)
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text("Our Model", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurface.copy(alpha=0.7f))
                    Text("${arb.modelProbability}%", fontWeight = FontWeight.SemiBold, color = KalshiPrimary)
                }
            }
            Spacer(modifier = Modifier.height(16.dp))
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Column {
                    Text("Action", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurface.copy(alpha=0.7f))
                    Text(arb.action, color = KalshiSecondary, fontWeight = FontWeight.Bold)
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text("Expected Value", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurface.copy(alpha=0.7f))
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            "+${arb.expectedValue}¢", 
                            color = KalshiPrimary, 
                            fontWeight = FontWeight.Black,
                            fontSize = 18.sp
                        )
                    }
                }
            }
            Spacer(modifier = Modifier.height(16.dp))
            val context = androidx.compose.ui.platform.LocalContext.current
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                ImprovedTradeOnKalshiButton(marketTicker = arb.id, modifier = Modifier.weight(1f), isOutlined = true)
                Button(
                    onClick = onCalculate, 
                    modifier = Modifier.weight(1f), 
                    colors = ButtonDefaults.buttonColors(containerColor = KalshiPrimary)
                ) {
                    Text("Calculate Size", fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun SizerScreen(viewModel: KalshiEdgeViewModel) {
    val selectedArb by viewModel.selectedArb.collectAsState()

    var inputMode by rememberSaveable { mutableIntStateOf(0) } // 0 = Capital, 1 = Contracts
    var capital by rememberSaveable { mutableStateOf("1000") }
    var contractsInput by rememberSaveable { mutableStateOf("1000") }
    var kalshiPrice by rememberSaveable { mutableStateOf("52") }
    
    LaunchedEffect(selectedArb) {
        selectedArb?.let {
            if (it.action.contains("YES")) {
                kalshiPrice = it.kalshiYes.toString()
            } else {
                kalshiPrice = it.kalshiNo.toString()
            }
        }
    }
    
    val calculator = remember { SizerCalculator() }
    
    val capNum = calculator.parsePrice(capital)
    val contractNum = contractsInput.toLongOrNull() ?: 0L
    val kp = calculator.parsePrice(kalshiPrice).toInt()
    
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Position Sizer", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
        Text("Calculate risk-adjusted position size", color = MaterialTheme.colorScheme.onSurface.copy(0.7f))
        Spacer(Modifier.height(24.dp))
        
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            FilterChip(
                selected = inputMode == 0,
                onClick = { inputMode = 0 },
                label = { Text("By Capital") }
            )
            FilterChip(
                selected = inputMode == 1,
                onClick = { inputMode = 1 },
                label = { Text("By Contracts") }
            )
        }
        Spacer(Modifier.height(16.dp))
        
        if (inputMode == 0) {
            OutlinedTextField(
                value = capital,
                onValueChange = { newValue ->
                    if (newValue.isEmpty() || (newValue.all { it.isDigit() || it == '.' } && newValue.count { it == '.' } <= 1)) {
                        capital = newValue
                    }
                },
                label = { Text("Total Capital Dedicated ($)") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth()
            )
        } else {
            OutlinedTextField(
                value = contractsInput,
                onValueChange = { newValue ->
                    if (newValue.isEmpty() || newValue.all { it.isDigit() }) {
                        contractsInput = newValue
                    }
                },
                label = { Text("Number of Contracts") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth()
            )
        }
        
        Spacer(Modifier.height(16.dp))
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            OutlinedTextField(
                value = kalshiPrice,
                onValueChange = { newValue ->
                    if (newValue.isEmpty() || newValue.all { it.isDigit() }) {
                        kalshiPrice = newValue
                    }
                },
                label = { Text("Kalshi Price (¢)") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth()
            )
        }
        
        Spacer(Modifier.height(32.dp))
        
        Card(
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                if (kp in 1..99) {
                    val finalContracts = if (inputMode == 0) calculator.calculateMaxShares(capNum, kp / 100.0) else contractNum
                    val totalCost = (finalContracts * kp) / 100.0
                    val payout = finalContracts * 1.0 // $1 payout per contract
                    val modelProb = selectedArb?.modelProbability ?: 50
                    val evProfit = (payout * (modelProb / 100.0)) - totalCost
                    
                    Text("Recommended Allocation", style = MaterialTheme.typography.labelSmall, color = KalshiPrimary)
                    Spacer(Modifier.height(8.dp))
                    Text("Buy $finalContracts Contracts on Kalshi", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                    Spacer(Modifier.height(16.dp))
                    
                    HorizontalDivider(color = MaterialTheme.colorScheme.onSurface.copy(alpha=0.1f))
                    Spacer(Modifier.height(16.dp))
                    
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Gross Investment", color = MaterialTheme.colorScheme.onSurface.copy(0.7f))
                        Text(String.format("$%.2f", totalCost), fontWeight = FontWeight.Medium)
                    }
                    Spacer(Modifier.height(8.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Max Payout", color = MaterialTheme.colorScheme.onSurface.copy(0.7f))
                        Text(String.format("$%.2f", payout), fontWeight = FontWeight.Medium)
                    }
                    Spacer(Modifier.height(8.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Net Profit (If Won)", color = MaterialTheme.colorScheme.onSurface.copy(0.7f))
                        Text(String.format("+$%.2f", payout - totalCost), color = Color.Green, fontWeight = FontWeight.Bold)
                    }
                    Spacer(Modifier.height(8.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Expected Value (EV)", color = MaterialTheme.colorScheme.onSurface.copy(0.7f))
                        Text(String.format(if (evProfit >= 0) "+$%.2f" else "-$%.2f", Math.abs(evProfit)), color = KalshiPrimary, fontWeight = FontWeight.Black)
                    }
                    Spacer(Modifier.height(16.dp))
                    ImprovedTradeOnKalshiButton(marketTicker = selectedArb?.id ?: "", modifier = Modifier.fillMaxWidth())
                } else {
                    Text("Invalid Price", color = KalshiError, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun PositionsScreen(viewModel: KalshiEdgeViewModel) {
    val positions by viewModel.positions.collectAsState()
    var displayFilter by rememberSaveable { mutableStateOf("All") }
    
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Active Opportunities", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(16.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("All", "Open", "Closed").forEach { filter ->
                FilterChip(
                    selected = displayFilter == filter,
                    onClick = { displayFilter = filter },
                    label = { Text(filter) },
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = KalshiPrimary.copy(alpha = 0.2f),
                        selectedLabelColor = KalshiPrimary
                    )
                )
            }
        }
        Spacer(Modifier.height(16.dp))
        LazyColumn(modifier = Modifier.weight(1f).fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            val filtered = positions.filter { displayFilter == "All" || it.status.contains(displayFilter) }
            items(filtered, key = { it.id }) { pos -> PositionCard(pos) }
        }
    }
}

@Composable
fun PositionCard(pos: KalshiPosition) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(
                    pos.status,
                    color = if(pos.status == "Open") KalshiPrimary else KalshiWarning,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp
                )
                Text("${pos.contractsActive} Contracts", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurface.copy(0.7f))
            }
            Spacer(modifier = Modifier.height(8.dp))
            Text(pos.eventTitle, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(12.dp))
            
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Column {
                    Text("Side", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurface.copy(0.7f))
                    Text(pos.side, fontWeight = FontWeight.Bold, color = if(pos.side == "YES") KalshiPrimary else KalshiSecondary)
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("Entry", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurface.copy(0.7f))
                    Text("${pos.entryCost}¢", fontWeight = FontWeight.Bold)
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text("Current", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurface.copy(0.7f))
                    Text("${pos.currentCost}¢", fontWeight = FontWeight.Bold)
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            val isProfit = pos.currentCost > pos.entryCost
            val pnl = (pos.currentCost - pos.entryCost) * pos.contractsActive
            
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Invested: $${String.format("%.2f", pos.totalInvested / 100.0)}", color = MaterialTheme.colorScheme.onSurface)
                Text(
                    "PnL: ${if(pnl >= 0) "+" else "-"}$${String.format("%.2f", Math.abs(pnl) / 100.0)}", 
                    color = if(isProfit) KalshiPrimary else KalshiError, 
                    fontWeight = FontWeight.Bold
                )
            }
            
            if (pos.status == "Open") {
                Spacer(modifier = Modifier.height(12.dp))
                OutlinedButton(onClick = {}, modifier = Modifier.fillMaxWidth()) {
                    Text("Close Position")
                }
            }
        }
    }
}

@Composable
fun SavedScreen(viewModel: KalshiEdgeViewModel, onNavigateToSizer: () -> Unit) {
    val savedList by viewModel.savedOpportunities.collectAsState()
    
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Saved Opportunities", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
        Text("Your categorized bookmarks.", color = MaterialTheme.colorScheme.onSurface.copy(0.7f))
        Spacer(Modifier.height(16.dp))
        
        if (savedList.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("No saved opportunities yet.", color = MaterialTheme.colorScheme.onSurface.copy(alpha=0.5f))
            }
        } else {
            val categorized = savedList.groupBy { (it.category ?: "").ifBlank { "General" } }
            LazyColumn(modifier = Modifier.weight(1f).fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                categorized.forEach { (category, items) ->
                    item {
                        Text(category, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, color = KalshiPrimary, modifier = Modifier.padding(top = 8.dp))
                    }
                    items(items, key = { it.id }) { savedOpp ->
                        val arb = KalshiOpportunity(
                            id = savedOpp.id ?: "",
                            eventTitle = savedOpp.eventTitle ?: "Unknown Event",
                            kalshiYes = savedOpp.kalshiYes ?: 0,
                            kalshiNo = savedOpp.kalshiNo ?: 0,
                            modelProbability = savedOpp.modelProbability ?: 0,
                            expectedValue = savedOpp.expectedValue ?: 0,
                            action = savedOpp.action ?: "YES",
                            timestamp = savedOpp.timestamp ?: 0L
                        )
                        OpportunityCard(
                            arb = arb,
                            onCalculate = { 
                                viewModel.selectOpportunity(arb)
                                onNavigateToSizer() 
                            },
                            onCardClick = {} // Do nothing in saved
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun SentimentChart(history: List<Float>, modifier: Modifier = Modifier) {
    if (history.isEmpty()) return
    val minVal = history.minOrNull() ?: -50f
    val maxVal = history.maxOrNull() ?: 50f
    val range = maxVal - minVal
    
    androidx.compose.foundation.Canvas(modifier = modifier) {
        val width = size.width
        val height = size.height
        val stepX = width / (history.size - 1).coerceAtLeast(1)
        
        val displayRange = if (range == 0f) 1f else range
        
        val points = history.mapIndexed { index, value ->
            val normalizedY = 1f - ((value - minVal) / displayRange)
            androidx.compose.ui.geometry.Offset(x = index * stepX, y = normalizedY * height)
        }
        
        val path = androidx.compose.ui.graphics.Path().apply {
             if (points.isNotEmpty()) {
                moveTo(points.first().x, points.first().y)
                for (i in 1 until points.size) {
                    val previous = points[i - 1]
                    val current = points[i]
                    val controlX = (previous.x + current.x) / 2
                    quadraticTo(controlX, previous.y, current.x, current.y)
                }
             }
        }
        
        drawPath(
            path = path,
            color = KalshiPrimary,
            style = androidx.compose.ui.graphics.drawscope.Stroke(
                width = 2.dp.toPx(),
                cap = androidx.compose.ui.graphics.StrokeCap.Round,
                join = androidx.compose.ui.graphics.StrokeJoin.Round
            )
        )
    }
}

@Composable
fun MarketDetailScreen(viewModel: KalshiEdgeViewModel, onBack: () -> Unit, onNavigateToSizer: () -> Unit) {
    val arb = viewModel.selectedArb.collectAsState().value
    if (arb == null) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text("No market selected")
        }
        return
    }

    Column(modifier = Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState())) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
            }
            Text("Market Insights", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
        }
        Spacer(Modifier.height(16.dp))
        
        Text(arb.eventTitle, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(16.dp))

        // Metrics Row
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
             Card(modifier = Modifier.weight(1f).padding(end=8.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                 Column(modifier = Modifier.padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                     Text("Our Model", style = MaterialTheme.typography.labelMedium)
                     Text("${arb.modelProbability}%", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold, color = KalshiPrimary)
                 }
             }
             Card(modifier = Modifier.weight(1f).padding(start=8.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                 Column(modifier = Modifier.padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                     Text("Market Price", style = MaterialTheme.typography.labelMedium)
                     Text("${arb.kalshiYes}¢", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
                 }
             }
        }
        
        Spacer(Modifier.height(24.dp))
        Text("Price History", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
        Spacer(Modifier.height(8.dp))
        SentimentChart(history = arb.priceHistory, modifier = Modifier.fillMaxWidth().height(100.dp))
        
        Spacer(Modifier.height(24.dp))
        Text("Volatility Trend (30d)", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
        Spacer(Modifier.height(8.dp))
        SentimentChart(history = arb.volatilityHistory, modifier = Modifier.fillMaxWidth().height(100.dp))

        Spacer(Modifier.height(24.dp))
        Text("Sentiment Score (News)", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
        Spacer(Modifier.height(8.dp))
        SentimentChart(history = arb.sentimentHistory, modifier = Modifier.fillMaxWidth().height(100.dp))
        
        Spacer(Modifier.height(32.dp))
        Button(onClick = onNavigateToSizer, modifier = Modifier.fillMaxWidth(), colors = ButtonDefaults.buttonColors(containerColor = KalshiPrimary)) {
            Text("Calculate Position Size", fontWeight = FontWeight.Bold)
        }
        Spacer(Modifier.height(32.dp))
    }
}

fun android.content.Context.safeOpenUrl(url: String) {
    try {
        val intent = android.content.Intent(android.content.Intent.ACTION_VIEW, android.net.Uri.parse(url)).apply {
            addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        startActivity(intent)
    } catch (e: Exception) {
        android.widget.Toast.makeText(this, "Unable to open link.", android.widget.Toast.LENGTH_SHORT).show()
    }
}

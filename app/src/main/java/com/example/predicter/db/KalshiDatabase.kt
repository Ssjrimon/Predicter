package com.example.predicter.db

import androidx.room.Dao
import androidx.room.Database
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.RoomDatabase
import com.example.predicter.data.SavedOpportunity
import kotlinx.coroutines.flow.Flow

@Dao
interface OpportunityDao {
    @Query("SELECT * FROM saved_opportunities ORDER BY timestamp DESC")
    fun getAllSaved(): Flow<List<SavedOpportunity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOpportunity(opportunity: SavedOpportunity)

    @Query("DELETE FROM saved_opportunities WHERE id = :id")
    suspend fun deleteOpportunity(id: String)
}

@Database(entities = [SavedOpportunity::class], version = 1, exportSchema = false)
abstract class KalshiDatabase : RoomDatabase() {
    abstract fun opportunityDao(): OpportunityDao
}

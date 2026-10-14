package studio.bleca.binux

import android.content.Context
import androidx.room.*

@Entity(tableName="sessions")
data class SessionRecord(@PrimaryKey val id: String, val cwd: String, val pid: Int, val state: String, val updated: Long, val transcript: String)
@Entity(tableName="jobs")
data class JobRecord(@PrimaryKey val id: String, val argv: String, val cwd: String, val pid: Int, val state: String, val started: Long, val log: String, val server: String?, val exit: Int?)
@Dao
interface JobDao {
 @Insert(onConflict=OnConflictStrategy.REPLACE) fun save(record: JobRecord)
 @Query("SELECT * FROM jobs ORDER BY started DESC LIMIT 200") fun history(): List<JobRecord>
 @Query("SELECT * FROM jobs WHERE id=:id") fun get(id: String): JobRecord?
 @Query("UPDATE jobs SET state='interrupted', pid=-1 WHERE state IN ('running','paused','stopping')") fun markInterrupted()
}
@Dao
interface SessionDao {
 @Insert(onConflict=OnConflictStrategy.REPLACE) fun save(record: SessionRecord)
 @Query("SELECT * FROM sessions ORDER BY updated DESC LIMIT 40") fun history(): List<SessionRecord>
 @Query("UPDATE sessions SET state='interrupted', pid=-1 WHERE state='running'") fun markInterrupted()
}
@Database(entities=[SessionRecord::class,JobRecord::class],version=1,exportSchema=true)
abstract class BinuxDatabase: RoomDatabase() {
 abstract fun sessions(): SessionDao
 abstract fun jobs(): JobDao
 companion object { fun open(context: Context) = Room.databaseBuilder(context,BinuxDatabase::class.java,"binux.db").build() }
}

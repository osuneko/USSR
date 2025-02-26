from typing import (
    Optional,
    Tuple,
    Union
)
import aiomysql
import asyncio

class MySQLPool:
    """The wrapper around the `aiomysql` module. It allows for
    the simple usage of the database within many circumstances while
    respecting the one connection at a time rule.
    
    Creating a wrapper as such allows us to quickly change the module used for
    MySQL without rewriting a large portion of the codebase.
    Classmethods:
        connect: Creates a connection to the MySQL server and establishes a
            pool.
    """

    __slots__ = ("_pool",)

    def __init__(self):
        """Creates the default values for the connector. Use the `conntect`
        classmethod instead."""
        self._pool: aiomysql.Pool
    
    @classmethod
    async def connect(
        self,
        host: str,
        user: str,
        password: str,
        database: str,
        port: int = 3306
    ):
        """Creates the MySQL connecton pool. Handles authentication and the
        configuration of the object.
        
        Note:
            Calling this function allows for the usage of all functions within
                this class, such as `fetchone`.
        
        Args:
            host (str): The hostname of the MySQL server you would like to
                connect. Usually `localhost`.
            user (str): The username of the MySQL user you would like to log
                into.
            password (str): The password of the MySQL user you would like to
                log into.
            database (str): The database you would like to interact with.
            port (int): The port at which the MySQL server is located at.
                Default set to 3306.
        """

        # Ok so here we create the pool.
        self._pool = await aiomysql.create_pool(
            host= host,
            port= port,
            user= user,
            password= password,
            db = database,
            pool_recycle= False, # Causes rather large issues.
        )
    
    async def fetchone(self, query: str, args: tuple = ()) -> Optional[tuple]:
        """Executes `query` in MySQL and returns the first result.
        
        Args:
            query (str): The MySQL query to be executed.
            args (tuple, list): The list or tuple of arguments to be safely
                formatted into the query.
        
        Returns:
            Tuple in the arrangement specified within the query if a result is
                found.
            None if no results are found.
        """

        # Fetch a connection from the pool.
        async with self._pool.acquire() as pool:
            # Grab a cur.
            async with pool.cursor() as cur:
                # Execute and fetchone.
                await cur.execute(query, args)

                # Immidiately return it
                return await cur.fetchone()
    
    async def fetchcol(self, query: str, args: tuple = ()) -> Optional[Union[int, str]]:
        """Fetches the value of a singular column from the result.
        
        Args:
            query (str): The MySQL query to be executed.
            args (tuple, list): The list or tuple of arguments to be safely
                formatted into the query.
        
        Note:
            This is simply a wrapper around `fetchone` with unpacking.
        """

        res = await self.fetchone(query, args)

        return res[0] if res else None
    
    async def fetchall(self, query: str, args: tuple = ()) -> Tuple[tuple]:
        """Executes `query` in MySQL and returns all of the found results.
        
        Args:
            query (str): The MySQL query to be executed.
            args (tuple, list): The list or tuple of arguments to be safely
                formatted into the query.
        
        Returns:
            Tuple of tuples with the results found.
            
        """

        # Fetch a connection from the pool.
        async with self._pool.acquire() as pool:
            # Grab a cur.
            async with pool.cursor() as cur:
                # Execute and fetchall.
                await cur.execute(query, args)

                # Immidiately return it
                return await cur.fetchall()
        
    async def execute(self, query: str, args: tuple = ()) -> int:
        """Simply executes `query` and commits all changes made by it to
        database.
        
        Note:
            Please don't use this function for select queries. For them rather
                use `fetchall` and `fetchone`
        
        Args:
            query (str): The MySQL query to be executed.
            args (tuple, list): The list or tuple of arguments to be safely
                formatted into the query.
        
        Returns:
            The ID of the last row affected.
        """

         # Fetch a connection from the pool.
        async with self._pool.acquire() as pool:
            # Grab a cur.
            async with pool.cursor() as cur:
                # Execute it.
                await cur.execute(query, args)

                # Commit it.
                await pool.commit()

                # Return it
                return cur.lastrowid

    def kill(self) -> None:
        """Ends the MySQL connection pool to the MySQL server.
        
        Note:
            As the name suggests, this fully terminates the connection. This
                means that no MySQL queries may be ran following the execution
                of this coro.
        """

        self._pool.terminate()
        self._pool.close()

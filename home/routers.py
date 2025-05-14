class DatabaseRouter:
    """
    Router para manejar la base de datos local
    """
    def db_for_read(self, model, **hints):
        """
        Lee de la base de datos default (local)
        """
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Escribe en la base de datos default (local)
        """
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Permite relaciones en la misma base de datos
        """
        if obj1._state.db == 'default' and obj2._state.db == 'default':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Asegura que las migraciones se apliquen a la base de datos
        """
        return True
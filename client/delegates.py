import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import multiprocessing

from . import messages


class Delegate(object):
    """Parent class for all delegates
    
    Defines general methods that should be available for all delegates
    
    Attributes:
        _client (Client): Client delegate is attached to
        info (Message): Message containing all info on delegate
        specifier (str): Keyword specifying delegate in state
        methods (list): List of avalilable methods to help UI
    """

    def __init__(self, client, message, specifier):
        self._client = client
        self.info = message
        self.specifier = specifier
    
    def __repr__(self):
        return f"{self.specifier} delegate | {self.info.id}"

    # For all except Document Delegate
    def on_new(self, message):
        pass

    # For Document, Table, Entity, Plot, Material, Light Delegates
    def on_update(self, message):
        pass

    # For all except Document Delegate
    def on_remove(self, message):
        pass


    def show_methods(self):
        """Show methods available on this delegate"""

        print(f"-- Methods on {self} --")
        print("--------------------------------------")
        for name in self.__all__:
            method = getattr(self, name)
            print(f">> '{name}'\n{method.__doc__}")


class InjectedMethod(object):
    """Class for representing injected method in delegate

    Attributes:
        method (method): method to be called
        injected (bool): attribute marking method as injected
    """

    def __init__(self, method_obj) -> None:
        self.method = method_obj
        self.injected = True

    def __call__(self, *args, **kwds):
        self.method(*args, **kwds)


class LinkedMethod(object):
    """Class linking target delegate and method's delegate 
        
    make a cleaner function call in injected method
    
    Attributes:
        _obj_delegate (delegate): 
            delgate method is being linked to
        _method_delegate (MethodDelegate): 
            the method's delegate 
    """

    def __init__(self, object_delegate: Delegate, method_delegate: Delegate):
        self._obj_delegate = object_delegate
        self._method_delegate = method_delegate

    def __call__(self, on_done=None, *arguments):
        self._method_delegate.invoke(self._obj_delegate, arguments, callback=on_done)


def inject_methods(delegate: Delegate, methods: list):
    """Inject methods into a delegate class

    Args:
        delegate_name (str): 
            identifier for delegate to be modified
        methods (list): 
            list of method id's to inject
    """

    # Clear out old injected methods
    for name in dir(delegate):
        att = getattr(delegate, name)
        if hasattr(att, "injected"):
            print(f"Deleting: {name} in inject methods")
            delattr(delegate, name)

    state_methods = delegate._client.state["methods"] 
    for id in methods:

        # Get method delegate and manipulate name to exclude noo::
        method = state_methods[tuple(id)]
        name = method.info.name[5:]

        # Create injected by linking delegates, and creating call method
        linked = LinkedMethod(delegate, method)
        injected = InjectedMethod(linked.__call__)

        setattr(delegate, name, injected)


def inject_signals(delegate: Delegate, signals: list):
    """Method to inject signals into delegate

    Args:
        delegate (delegate): 
            delegate object to be injected 
        signals (list): 
            list of signal id's to be injected
    """

    state_signals = delegate._client.state["signals"]
    injected_signals = {}
    for id in signals:
        signal = state_signals[tuple(id)]
        injected_signals[signal.info.name] = signal.info
    delegate.signals = injected_signals



"""
Default Delegates for Python Client
"""

class MethodDelegate(Delegate):
    """Delegate representing a method which can be invoked on the server

    Attributes:
        _client (client object): 
            client delegate is a part of 
        info (message): 
            message containing information on the method
        specifier (str): 
            keyword for specifying the type of delegate
        context_map (dict):
            mapping specifier to context for method invocation
    """

    def __init__(self, client, message, specifier):
        self._client = client
        self.info = message
        self.specifier = specifier
        self.context_map = {
            "tables": "table",
            "plots": "plot",
            "entities": "entity"
        }

    def on_new(self, message):
        pass

    def on_remove(self):
        pass

    def invoke(self, on_delegate, args = None, callback = None):
        """Invoke this delegate's method

        Args:
            on_delegate (delegate):
                delegate method is being invoked on 
                used to get context
            args (list, optional):
                args for the method
            callback (function):
                function to be called when complete
        """
        context = {self.context_map[on_delegate.specifier]: on_delegate.info.id}
        self._client.invoke_method(self.info.id, args, context = context, callback = callback)


    def __repr__(self):
        """Custom string representation for methods"""
        
        rep = f"{self.info.name}:\n\t{self.info.doc}\n\tReturns: {self.info.return_doc}\n\tArgs:"
        for arg in self.info.arg_doc:
            rep += f"\n\t\t{arg.name}: {arg.doc}"
        return rep


class SignalDelegate(Delegate):
    """Delegate representing a signal coming from the server

    Attributes:
        _client (Client): 
            client delegate is a part of 
        info (message): 
            message containing information on the signal
        specifier (str): 
            keyword for specifying the type of delegate
    """
    
    def __init__(self, client, message, specifier):
        self._client = client
        self.info = message
        self.specifier = specifier

    def on_new(self, message):
        pass

    def on_remove(self, message): 
        pass


class SelectionRange(tuple):
    """Selection of range of rows"""

    def __new__(cls, key_from, key_to):
        return super().__new__(SelectionRange, (key_from, key_to))


class Selection(object):
    """Selection of certain rows in a table

    Attributes:
        name (str): 
            name of the selection
        rows (list[int]): 
            list of indices of rows
        row_ranges (list[SelectionRange]): 
            ranges of selected rows
    """

    def __init__(self, name: str, rows: list[int] = None, row_ranges: list[SelectionRange] = None) -> None:
        self.name = name
        self.rows = rows
        self.row_ranges = row_ranges

    def __repr__(self) -> str:
        return f"Selection Object({self.__dict__})"

    def __getitem__(self, attribute):
        return getattr(self, attribute)


class TableDelegate(Delegate):
    """Delegate representing a table

    Each table delegate corresponds with a table on the server
    To use the table, you must first subscribe 

    Attributes:
        _client (Client): 
            weak ref to client to invoke methods and such
        dataframe (Dataframe): 
            dataframe representing current state of the table
        selections (dict): 
            mapping of name to selection object
        signals (signals): 
            mapping of signal name to function
        name (str): 
            name of the table
        id (list): 
            id group for delegate in state and table on server
    """

    def __init__(self, client, message, specifier):
        super().__init__(client, message, specifier)
        self.dataframe = None
        self.name = "Table Delegate"
        self.selections = {}
        self.signals = {
            "tbl_reset" : self._reset_table,
            "tbl_rows_removed" : self._remove_rows,
            "tbl_updated" : self._update_rows,
            "tbl_selection_updated" : self._update_selection
        }
        # Specify public methods 
        self.__all__ = [
            "subscribe", 
            "request_clear", 
            "request_insert", 
            "request_remove", 
            "request_update", 
            "request_update_selection",
            "plot"
        ]
        self.plotting = None


    def _on_table_init(self, init_info):
        """Creates table from server response info

        Args:
            init_info (Message Obj): 
                Server response to subscribe which has columns, keys, data, 
                and possibly selections
        """

        data_dict = {getattr(col, "name"): data for col, data in zip(
            getattr(init_info, "columns"), getattr(init_info, "data"))}
        self.dataframe = pd.DataFrame(data_dict, index=getattr(init_info, "keys"))

        # Initialize selections if any
        selections = getattr(init_info, "selections", [])
        for selection in selections:
            self.selections[selection.name] = selection
        
        print(f"Initialized data table...\n{self.dataframe}")


    def _reset_table(self):
        """Reset dataframe and selections to blank objects

        Method is linked to 'tbl_reset' signal
        """

        self.dataframe = pd.DataFrame()
        self.selections = {}

        if self.plotting:
            self._update_plot()


    def _remove_rows(self, key_list):
        """Removes rows from table

        Method is linked to 'tbl_rows_removed' signal

        Args:
            key_list (list): list of keys corresponding to rows to be removed
        """

        self.dataframe.drop(index=key_list, inplace=True)
        print(f"Removed Rows: {key_list}...\n", self.dataframe)

        if self.plotting:
            self._update_plot()


    def _update_rows(self, keys: list, cols: list):
        """Update rows in table

        Method is linked to 'tbl_updated' signal

        Args:
            keys (list): 
                list of keys to update
            cols (list): 
                list of cols containing the values for each new row,
                should be col for each col in table, and value for each key
        """

        headers = self.dataframe.columns.values
        new_df = pd.DataFrame({col: data for col, data in zip(
            headers, cols)}, index=keys)
        new_df_filled = new_df.combine_first(self.dataframe) # changes order of columns - problem?
        self.dataframe = new_df_filled

        if self.plotting:
            self._update_plot()
    
        print(f"Updated Rows...{keys}\n", self.dataframe)
        

    def _update_selection(self, selection_obj: Selection):
        """Change selection in delegate's state to new selection object

        Method is linked to 'tbl_selection_updated' signal

        Args:
            selection_obj (Selection): 
                obj with new selections to replace obj with same name
        """

        self.selections[selection_obj.name] = selection_obj
        print(f"Made selection {selection_obj.name} = {selection_obj}")
        

    def get_selection(self, name):
        """Get a selection object and construct Dataframe representation

        Args:
            name (str) : name of selection object to get
        """
        # Try to retrieve selection object from instance or return blank frame
        try:
            sel_obj = self.selections[name]
        except:
            return pd.DataFrame(columns=self.dataframe.columns)

        frames = []

        # Get rows already in that selection
        if sel_obj.rows:
            frames.append(self.dataframe.loc[sel_obj["rows"]])

        # Uses ranges in object to get other rows
        if sel_obj.row_ranges:
            ranges = sel_obj["row_ranges"]
            for r in ranges:
                frames.append(self.dataframe.loc[r[0]:r[1]-1])

        # Return frames concatenated
        df = pd.concat(frames)
        print(f"Got selection for {sel_obj}\n{df}")
        return df


    def _relink_signals(self):
        """Relink the signals for built in methods

        These should always be linked, along with whatever is injected,
        so relink on new and on update messages
        """

        self.signals["tbl_reset"] = self._reset_table
        self.signals["tbl_rows_removed"] = self._remove_rows
        self.signals["tbl_updated"] = self._update_rows
        self.signals["tbl_selection_updated"] = self._update_selection


    def on_new(self, message: messages.Message):
        """Handler when create message is received

        Args:
            message (Message): create message with the table's info
        """
        
        # Set name
        name = message["name"]
        methods = message["methods_list"]
        signals = message["signals_list"]
        if name: self.name = name
    
        # Inject methods and signals
        if methods: inject_methods(self, methods)
        if signals: inject_signals(self, signals)

        # Reset
        self._reset_table()
        self._relink_signals()

    def on_update(self, message):
        """Handler when update message is received
        
        Args:
            message (Message): update message with the new table's info
        """

        self._relink_signals()
        # update dataframe
    

    def on_remove(self):
        pass


    def subscribe(self):
        """Subscribe to this delegate's table

        Calls on_table_init as callback
        
        Raises:
            Exception: Could not subscribe to table
        """

        try:
            self.tbl_subscribe(on_done=self._on_table_init)
        except:
            raise Exception("Could not subscribe to table")

    
    def request_insert(self, col_list: list=None, row_list: list=None, on_done=None):
        """Add rows to end of table

        User endpoint for interacting with table and invoking method

        Args:
            col_list (list, optional): add rows as list of columns
            row_list (list, optional): add rows using list of rows
            on_done (function, optional): callback function
        """

        if col_list is not None:
            self.tbl_insert(on_done, col_list)
        elif row_list is not None:
            self.tbl_insert(on_done, np.transpose(row_list).tolist())

    def request_update(self, data_frame: pd.DataFrame, on_done=None):
        """Update the table using a DataFrame

        User endpoint for interacting with table and invoking method

        Args:
            data_frame (DataFrame):
                data frame containing the values to be updated
            on_done (function, optional): 
                callback function called when complete
        """
        
        if len(data_frame.columns) != len(self.dataframe.columns):
            raise Exception(
                "Dataframes should have the same number of columns")
        
        col_list = []
        for col in list(data_frame):
            col_list.append(data_frame[col].tolist())
        self.tbl_update(on_done, data_frame.index.to_list(), col_list)

    def request_remove(self, keys: list, on_done=None):
        """Remove rows from table by their keys

        User endpoint for interacting with table and invoking method

        Args:
            keys (list):
                list of keys for rows to be removed
            on_done (function, optional): 
                callback function called when complete
        """

        self.tbl_remove(on_done, keys)

    def request_clear(self, on_done=None):
        """Clear the table

        User endpoint for interacting with table and invoking method

        Args:
            on_done (function, optional): callback function called when complete
        """
        self.tbl_clear(on_done)

    def request_update_selection(self, name: str, keys: list, on_done=None):
        """Update a selection object in the table

        User endpoint for interacting with table and invoking method

        Args:
            name (str):
                name of the selection object to be updated
            keys (list):
                list of keys to be in new selection
            on_done (function, optional): 
                callback function called when complete
        """

        self.tbl_update_selection(on_done, name, {"rows": keys})


    def _update_plot(self):
        """Update plotting process when dataframe is updated"""

        df = self.dataframe
        self.sender.send(get_plot_data(df))


    def plot(self):
        """Creates plot in a new window

        Uses matplotlib to plot a representation of the table
        """

        self.sender, receiver = multiprocessing.Pipe()

        self.plotting=multiprocessing.Process(target=plot_process, args=(self.dataframe, receiver))
        self.plotting.start()


def get_plot_data(df: pd.DataFrame):
    """Helper function to extract data for the plot from the dataframe"""

    data = {
        "xs": df["x"], 
        "ys": df["y"], 
        "zs": df["z"],
        "s" : [(((sx + sy + sz) / 3) * 1000) for sx, sy, sz in zip(df["sx"], df["sy"], df["sz"])],
        "c" : [(r, g, b) for r, g, b in zip(df["r"], df["g"], df["b"])]
    }
    return data


def on_close(event):
    """Event handler for when window is closed"""

    plt.close('all')


def plot_process(df: pd.DataFrame, receiver):
    """Process for plotting the table as a 3d scatter plot

    Args:
        df (DataFrame): 
            the data to be plotted
        receiver (Pipe connection object):
            connection to receive updates from root process
    """

    # Enable interactive mode
    plt.ion()

    # Make initial plot
    fig = plt.figure()
    fig.canvas.mpl_connect('close_event', on_close)
    ax = fig.add_subplot(projection='3d')
    data = get_plot_data(df)
    ax.scatter(**data)

    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')

    plt.draw()
    plt.pause(.001)

    # Update loop
    while True:

        # If update received, redraw the scatter plot
        if receiver.poll(.1):
            update = receiver.recv()
            plt.cla() # efficient? better way to set directly?
            ax.scatter(**update) 
            plt.pause(.001)

        # Keep GUI event loop going as long as window is still open
        elif plt.fignum_exists(fig.number):
            plt.pause(1)
        else:
            break


class DocumentDelegate(Delegate):
    pass
    
class EntityDelegate(Delegate):
    pass

class PlotDelegate(Delegate):
    pass

class MaterialDelegate(Delegate):
    pass

class GeometryDelegate(Delegate):
    pass

class LightDelegate(Delegate):
    pass

class ImageDelegate(Delegate):
    pass

class TextureDelegate(Delegate):
    pass

class SamplerDelegate(Delegate):
    pass

class BufferDelegate(Delegate):
    pass

class BufferViewDelegate(Delegate):
    pass

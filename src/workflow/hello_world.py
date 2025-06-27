from prefect import flow, tags

@flow(log_prints=True)
def hello(name: str = "Marvin") -> None:
    """Log a friendly greeting."""
    print(f"Hello, {name}!")
    
    
if __name__ == "__main__":
    # run the flow with default parameters
    with tags("test"): # This is a tag that we can use to filter the flow runs in the UI
        hello()  # Logs: "Hello, Marvin!"

        # run the flow with a different input
        hello("Marvin")  # Logs: "Hello, Marvin!"

        # run the flow multiple times for different people
        crew = ["Zaphod", "Trillian", "Ford"]

        for name in crew:
            hello(name)
            
        input("Press Enter to exit...")  # Keep the console open to see the logs

from prefect import flow


class MyClass:

    @flow
    def my_instance_method(self):
        return "Hello, from an instance method!"


    @flow
    @classmethod
    def my_class_method(cls):
        return "Hello, from a class method!"


    @flow
    @staticmethod
    def my_static_method():
        return "Hello, from a static method!"


#MyClass().my_instance_method()
#MyClass.my_class_method()
#MyClass.my_static_method()

"""

What just happened?
When we decorated our function with @flow, the function was transformed into a Prefect flow. Each time we called it:

Prefect registered the execution as a flow run
It tracked all inputs, outputs, and logs
It maintained detailed state information about the execution
Added tags to the flow run to make it easier to find when observing the flow runs in the UI
In short, we took a regular function and enhanced it with observability and tracking capabilities.

​
But why does this matter?
This simple example demonstrates Prefect’s core value proposition: taking regular Python code and enhancing it with production-grade orchestration capabilities. Let’s explore why this matters for real-world data workflows.

​
You can change the code and run it again
For instance, change the greeting message in the hello function to a different message and run the flow again. You’ll see your changes immediately reflected in the logs.

​
You can process more data
Add more names to the crew list or create a larger data set to process. Prefect will handle each execution and track every input and output.

​
You can run a more complex flow
The hello function is a simple example, but in its place imagine something that matters to you, like:

ETL processes that extract, transform, and load data
Machine learning training and inference pipelines
API integrations and data synchronization jobs
Prefect lets you orchestrate these operations effortlessly with automatic observability, error handling, and retries.

​
Key Takeaways
Remember that Prefect makes it easy to:

Transform regular Python functions into production-ready workflows with just a decorator
Get automatic logging, retries, and observability without extra code
Run the same code anywhere - from your laptop to production
Build complex data pipelines while maintaining simplicity
Track every execution with detailed logs and state information
The @flow decorator is your gateway to enterprise-grade orchestration - no complex configuration needed!



"""
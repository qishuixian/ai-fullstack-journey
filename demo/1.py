# my_module.py
def greet(name):
    return f"Hello, {name}!"

print(f"模块的 __name__ 是: {__name__}")

if __name__ == "__main__":
    print("这段代码只在直接运行时执行")
    print(greet("World"))
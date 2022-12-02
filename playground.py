def main():
    pass
    print("pass")


# Python code to illustrate
# Decorators with parameters in Python

def decorator_func(x, y):
    def Inner(func):
        def wrapper(*args, **kwargs):
            print("I like Geeksforgeeks")
            print("Summation of values - {}".format(x + y))

            func(*args, **kwargs)

        return wrapper

    return Inner


if __name__ == "__main__":

    # def decorator(func):
    #     def inner(*args, **kwargs):
    #         # body
    #         val = func(*args, **kwargs)
    #         return val
    #
    #     return inner
    #
    # # Not using decorator
    # def foo(*args, **kwargs):
    #     print("evoke foo", args, kwargs)
    #
    # # decorator demo
    # @decorator
    # def boo(*args, **kwargs):
    #     print("evoke boo", args, kwargs)
    #
    # # evoke method 1
    # decorator(foo)("foo-arg1", foo_k1="foo_v1")
    # # evoke method 2
    # boo("boo-arg1", boo_k1="boo_v1")


    def decorator_w_para(*dec_args, **dec_kwargs):
        def inner_1(func):
            def inner(*args, **kwargs):
                # body
                print("+++++position 2: evoke decorator_w_para", dec_args, dec_kwargs)
                val = func(*args, **kwargs)
                return val

            print("+++++position 3: evoke decorator_w_para", dec_args, dec_kwargs)
            return inner
        print("+++++position 1: evoke decorator_w_para", dec_args, dec_kwargs)
        return inner_1


    def decorator_w_para2(*dec_args, **dec_kwargs):
        def inner_1(func):
            # body
            print("no need to evoke inner funct, just print out type", func.__name__, type(func))
            # print("+++++position 3: evoke decorator_w_para", dec_args, dec_kwargs)
            return func
        print("+++++position 1: evoke decorator_w_para", dec_args, dec_kwargs)
        return inner_1

    # Not using decorator
    def foo2(*args, **kwargs):
        print("evoke foo", args, kwargs)

    # decorator demo
    # @decorator_w_para("decorator-arg1", decorator_k1="decorator_v1")
    @decorator_w_para2("decorator-arg1", decorator_k1="decorator_v1")
    def boo2(*args, **kwargs):
        print("evoke boo2", args, kwargs)


    # print("--------------")
    # # evoke method 1
    # decorator_w_para("decorator-arg1", decorator_k1="decorator_v1")(foo2)("foo-arg1", foo_k1="foo_v1")
    # print("--------------")
    # # evoke method 2
    print("--------------")
    boo2("boo-arg1", foo_k1="boo_v1")
    print("--------------")
    print(boo2)



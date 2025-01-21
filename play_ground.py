import os
import gevent
import logging
from volttrontesting.utils.utils import get_rand_vip
from volttrontesting.utils.platformwrapper import PlatformWrapper
from volttron.platform.auth.auth_file import AuthFile
# from volttrontesting.fixtures.volttron_platform_fixtures import cleanup_wrapper
from typing import Optional 
import psutil

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def build_wrapper(vip_address: str, should_start: bool = True, messagebus: str = 'zmq',
                  remote_platform_ca: Optional[str] = None,
                  instance_name: Optional[str] = None, agent_isolation_mode: bool = False, **kwargs):
    wrapper = PlatformWrapper(ssl_auth=kwargs.pop('ssl_auth', False),
                              messagebus=messagebus,
                              instance_name=instance_name,
                              agent_isolation_mode=agent_isolation_mode,
                              remote_platform_ca=remote_platform_ca,
                              auth_enabled=kwargs.pop('auth_enabled', True))
    if should_start:
        wrapper.startup_platform(vip_address=vip_address, **kwargs)
        if not wrapper.dynamic_agent:
            raise ValueError(f"Couldn't start platform successfully for {wrapper.messagebus}")
        assert wrapper.is_running()
    return wrapper

def cleanup_wrapper(wrapper):
    logger.info('Shutting down instance: %s, MESSAGE BUS: %s', wrapper.volttron_home, wrapper.messagebus)
    if not wrapper.is_running():
        return
    wrapper_pid = wrapper.p_process.pid
    wrapper.shutdown_platform()
    if wrapper.p_process is not None and psutil.pid_exists(wrapper_pid):
        proc = psutil.Process(wrapper_pid)
        proc.terminate()
    if not wrapper.debug_mode and Path(wrapper.volttron_home).exists():
        shutil.rmtree(Path(wrapper.volttron_home))
    if psutil.pid_exists(wrapper_pid):
        psutil.Process(wrapper_pid).kill()

def volttron_instance(request_param, **kwargs):
    """Returns a single instance of volttron platform for testing."""
    address = kwargs.pop("vip_address", get_rand_vip())
    if request_param['messagebus'] == 'rmq':
        kwargs['timeout'] = 240

    wrapper = build_wrapper(address,
                            messagebus=request_param.get('messagebus', 'zmq'),
                            ssl_auth=request_param.get('ssl_auth', False),
                            auth_enabled=request_param.get('auth_enabled', True),
                            **kwargs)

    try:
        return wrapper
    except Exception as ex:
        logger.error("Error creating volttron instance: %s", ex)
        cleanup_wrapper(wrapper)
        raise

def build_two_test_agents(volttron_instance):
    """Returns two agents for testing authorization."""
    agent1 = volttron_instance.build_agent(identity='agent1')
    gevent.sleep(1)
    agent2 = volttron_instance.build_agent(identity='agent2')
    gevent.sleep(1)

    agent1.foo = lambda x: x
    agent1.foo.__name__ = 'foo'

    agent1.vip.rpc.export(method=agent1.foo)
    agent1.vip.rpc.allow(agent1.foo, 'can_call_foo')

    try:
        return agent1, agent2
    finally:
        agent1.core.stop()
        agent2.core.stop()
        auth_file = AuthFile(os.path.join(volttron_instance.volttron_home, 'auth.json'))
        allow_entries = auth_file.read_allow_entries()
        auth_file.remove_by_indices(list(range(3, len(allow_entries))))
        gevent.sleep(1)

def main():
    request_param = dict(messagebus='zmq', ssl_auth=False)
    
    # Setup volttron_instance
    instance = volttron_instance(request_param)
    
    try:
        # Use the build_two_test_agents function
        agent1, agent2 = build_two_test_agents(instance)
        print(f"==============={agent2.publickey =}")
        instance.add_capabilities(agent2.publickey, 'can_call_foo')
        
        # Test the RPC call
        try:
            # result = agent1.vip.rpc.call('agent1', 'foo', 'can_call_foo').get(timeout=10)
            # result = agent2.vip.rpc.call('agent1', 'foo', 'test').get(timeout=10)
            result = agent2.vip.rpc.call(agent1.core.identity, 'foo', 1).get(timeout=1)
            assert result == 1
        except Exception as e:
            result = str(e)
        
        print("RPC Call Result:", result)
    finally:
        # Cleanup
        cleanup_wrapper(instance)

if __name__ == "__main__":
    main()

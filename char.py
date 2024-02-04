

def _calc_min_uuid_length(agents):
    agent_ids = [agent.uuid for agent in agents]
    return _calc_min_unique_uuid_length(agent_ids)


def _calc_min_unique_uuid_length(uuids: list) -> int:
    """
    Helper function to calculate unique uuids with minial char numbers.
    EXAMPLE:
    agent_ids = ['9b171ba5-f69f-4895-a69e-b51cf4d78150',
                 '2c7c8405-49c8-48eb-86ff-236ebe39da6e',
                 'd73a71c8-000f-46aa-8e5f-c4436cf847c3',
                 'da2c1f0d-6ce5-4095-843c-3abc861d5199',
                 'f5de325c-e723-41e5-9ceb-fae722a40eb6']
    _calc_min_unique_uuid_length(agent_ids)
    >> 2
    EXAMPLE:
    agent_ids = ['9b171ba5-f69f-4895-a69e-b51cf4d78150',
                 'd77c8405-49c8-48eb-86ff-236ebe39da6e',
                 'd73a71c8-000f-46aa-8e5f-c4436cf847c3',
                 'da2c1f0d-6ce5-4095-843c-3abc861d5199',
                 'da3c1f0d-6ce5-4095-843c-3abc861d5199',
                 'f5de325c-e723-41e5-9ceb-fae722a40eb6']
    _calc_min_unique_uuid_length(agent_ids)
    >> 3
    agent_ids = ['9b171ba5-f69f-4895-a69e-b51cf4d78150',
                 'd77c8405-49c8-48eb-86ff-236ebe39da6e',
                 'f5de325c-e723-41e5-9ceb-fae722a40eb6']
    _calc_min_unique_uuid_length(agent_ids)
    >> 1
    """
    # mechanism: start common_len at 1,
    # collect a pool of uuids represent by first common_len of its uuid,
    # increase the number of common_len until the pool of uuids with first common_len has unique members.
    common_len = 1
    while common_len <= len(uuids[0]):  # assuming all uuids have the same length
        head_uuids = [uuid[:common_len] for uuid in uuids]
        if len(head_uuids) == len(set(head_uuids)):
            break
        common_len += 1
    print(head_uuids)
    return common_len


if __name__ == "__main__":
    agent_ids = ['9b171ba5-f69f-4895-a69e-b51cf4d78150',
             '2c7c8405-49c8-48eb-86ff-236ebe39da6e',
             'd73a71c8-000f-46aa-8e5f-c4436cf847c3',
             'da2c1f0d-6ce5-4095-843c-3abc861d5199',
             'f5de325c-e723-41e5-9ceb-fae722a40eb6']
    agent_ids = ['9b171ba5-f69f-4895-a69e-b51cf4d78150',
                 'd77c8405-49c8-48eb-86ff-236ebe39da6e',
                 'd73a71c8-000f-46aa-8e5f-c4436cf847c3',
                 'da2c1f0d-6ce5-4095-843c-3abc861d5199',
                 'da3c1f0d-6ce5-4095-843c-3abc861d5199',
                 'f5de325c-e723-41e5-9ceb-fae722a40eb6']
    agent_ids = ['9b171ba5-f69f-4895-a69e-b51cf4d78150',
                 '9b171ba5-f69f-4895-a69e-b51cf4d78151',
                ]
    print("something")
    # uuid_len = 1
    # print([uuid[:uuid_len] for uuid in agent_ids])
    print(_calc_min_unique_uuid_length(agent_ids))



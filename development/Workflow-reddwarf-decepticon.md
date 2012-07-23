
Workflow for "reddwarf-decepticon"

#1 generate events based on end Times changes
* (RESIZE, DELETE, ...) - emits to AH
* CREATE events need to add records to our "usage" table

#2 Runs hourly, checks for >23 hr old events (EXISTS/Recurring events)
* works for > hourly resolution
* fixes to be at common cron time after 1st exists event
* if > 24, then we need to generate >1 event for each 24 hour period in the past

* create "usage" Table example:

| varchar   | timestamp(unixtime stamp)
|instance_id|end_time| volume_size | instance_size
|    1      | 4:07   |    1        |   512
|    2      | 14:17  |    2        |   1024

-------------------------------------------------------------------------------
EVENTS types
-------------------------------------------------------------------------------
- **reddwarf.instance.create**
  - message needs to be sent to the decepticon queue from the reddwarf lite task manager
  - message payload example

            {
                'method': "create_event",
                'args': {
                    'event_type': "reddwarf.instance.create",
                    'volume_size': 2,
                    'instance_size': 512,
                    'tenant_id': "123456",
                    'instance_id': 'asdf-qwert-reddwarf-id-2',
                    'instance_name': "my new db instance",
                    'launched_at': '2012-06-19T15:28:12Z',
                    'created_at': '2012-06-19T15:28:02Z',
                    'nova_instance_id': 'nova-instance-id-2',
                    'nova_volume_id': 'nova-volume-id-2',
                }
            }


* event_type: the name of the event that is being sent (string)
* tenant_id: Tenant ID that owns the this instance (string)
* instance_id: Reddwarf instance ID of this instance (string)
* nova_instance_id: Nova instance ID of this instance (string)
* instance_name: User selected display name for instance. (string)
* created_at: Timestamp for when this instance's record was created in Reddwarf/Nova (string, formatted "YYYY-MM-DD hh:mm:ss.ssssss")
* launched_at: Timestamp for when this instance was launched by hypervisor. (string, formatted "YYYY-MM-DD hh:mm:ss.ssssss") [when the guest is finished starting up on the instance]
* nova_volume_id: Nova volume ID of this volume (string)
* volume_size: size of disk allocation for this volume attached to this instance
* instance_size: memory allocation for this instance (in mb) (int)
* @instance_type: Name of the instance type ('flavor') of this instance. (string)
* @instance_type_id: Nova ID for instance type ('flavor') of this instance. (string) [TBD if needed?]
* @user_id: User ID that owns this instance (string)
* @image_ref_url: Image URL (from Glance) that this instance was created from. (string)
* @state: Current state of instance. (string, such as 'active' or 'deleted')
* @state_description: Additional human readable description of current state of instance.
* @fixed_ips: list of ip addresses (as strings) assigned to instance.

@ means that this atribute is not defined right now. Not sure if this will be needed.

- **reddwarf.instance.update_flavor/modify_flavor**
  - message payload example to decepticon

            {
                'method': "modify_event",
                'args': {
                    'event_type': "reddwarf.instance.modify_flavor",
                    'volume_size': 2,
                    'instance_size': 512,
                    'tenant_id': "123456",
                    'instance_id': 'asdf-qwert-reddwarf-id-2',
                    'instance_name': "my new db instance",
                    'launched_at': '2012-06-19T15:28:12Z',
                    'created_at': '2012-06-19T15:28:02Z',
                    'nova_instance_id': 'nova-instance-id-2',
                    'nova_volume_id': 'nova-volume-id-2',
                    'modify_at': '2012-06-19T15:28:12Z',
                }
            }

- **reddwarf.instance.update_volume/modify_volume**
  - message payload example to decepticon

            {
                'method': "modify_event",
                'args': {
                    'event_type': "reddwarf.instance.modify_volume",
                    'volume_size': 2,
                    'instance_size': 512,
                    'tenant_id': "123456",
                    'instance_id': 'asdf-qwert-reddwarf-id-2',
                    'instance_name': "my new db instance",
                    'launched_at': '2012-06-19T15:28:12Z',
                    'created_at': '2012-06-19T15:28:02Z',
                    'nova_instance_id': 'nova-instance-id-2',
                    'nova_volume_id': 'nova-volume-id-2',
                    'modify_at': '2012-06-19T15:28:12Z',
                }
            }

- **reddwarf.instance.delete**
  - message payload example to decepticon

            {
                'method': "delete_event",
                'args': {
                    'event_type': "reddwarf.instance.delete",
                    'volume_size': 2,
                    'instance_size': 512,
                    'tenant_id': "123456",
                    'instance_id': 'asdf-qwert-reddwarf-id-2',
                    'instance_name': "my new db instance",
                    'launched_at': '2012-06-19T15:28:12Z',
                    'created_at': '2012-06-19T15:28:02Z',
                    'nova_instance_id': 'nova-instance-id-2',
                    'nova_volume_id': 'nova-volume-id-2',
                    'deleted_at': '2012-06-19T15:28:12Z',
                }
            }

- **reddwarf.instance.exists**



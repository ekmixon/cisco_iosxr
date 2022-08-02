# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2016 Red Hat Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.iosxr.config import ConfigBase
from ansible.module_utils.network.iosxr.config.bgp import get_bgp_as
from ansible.module_utils.network.iosxr.config.bgp.network import BgpNetwork
from ansible.module_utils.network.iosxr.config.bgp.redistribute import BgpRedistribute


class BgpAddressFamily(ConfigBase):

    argument_spec = {
        'name': dict(choices=['ipv4', 'ipv6'], required=True),
        'cast': dict(choices=['flowspec', 'labeled-unicast', 'multicast', 'unicast'], default='unicast'),
        'networks': dict(type='list', elements='dict', options=BgpNetwork.argument_spec),
        'redistribute': dict(type='list', elements='dict', options=BgpRedistribute.argument_spec),
        'state': dict(choices=['present', 'absent'], default='present')
    }

    identifier = ('name', )

    def render(self, config=None):
        commands = []

        context = f'address-family {self.name}'
        if self.cast:
            context += f' {self.cast}'

        if config:
            if bgp_as := get_bgp_as(config):
                section = [f'router bgp {bgp_as}', context]
                config = self.get_section(config, section)

        if self.state == 'absent' and context in config:
            commands.append(f'no {context}')

        if self.state == 'present':
            subcommands = []
            for attr in self.argument_spec:
                if attr in self.values:
                    if meth := getattr(self, f'_set_{attr}', None):
                        if resp := meth(config):
                            subcommands.extend(to_list(resp))

            if subcommands:
                commands = [context, *subcommands, 'exit']
            elif not config or context not in config:
                commands.extend([context, 'exit'])

        return commands

    def _set_networks(self, config=None):
        commands = []
        for entry in self.networks:
            net = BgpNetwork(**entry)
            if resp := net.render(config):
                commands.append(resp)
        return commands

    def _set_redistribute(self, config=None):
        commands = []
        for entry in self.redistribute:
            redis = BgpRedistribute(**entry)
            if resp := redis.render(config):
                commands.append(resp)
        return commands

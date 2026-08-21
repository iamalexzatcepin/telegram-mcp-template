# Privacy

Telegram MCP runs locally under the user's operating-system account. The publisher does not operate a relay or receive Telegram credentials, sessions, messages, cache contents, tool inputs, or tool outputs.

The configured MCP client and its model provider may receive content returned by tools or included by the user in a prompt. Users should review that provider's privacy terms and enable only the capabilities and cache retention they need.

Telegram sessions are stored in the local OS keyring or an encrypted local file. Optional message cache and downloaded media remain local. Uninstalling the plugin does not automatically revoke Telegram sessions or delete local state; use the documented logout and cleanup steps, and revoke compromised sessions in Telegram `Settings → Devices`.


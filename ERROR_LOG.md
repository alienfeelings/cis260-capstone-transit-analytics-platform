Issues pushing to GitHub
=========================
ERROR:\
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists.
-----------------
SOLUTION:\
Open PowerShell as Administrator and run:
Get-Service ssh-agent

If it shows Stopped, run:\
Set-Service -Name ssh-agent -StartupType Automatic\
Start-Service ssh-agent

Then verify: Get-Service ssh-agent

You want:

Status   Name
------   ----
Running  ssh-agent

After that, back to PyCharm terminal:\
ssh-add $HOME\.ssh\"your-ssh-key"

Then: ssh-add -l

Test GitHub: ssh -T git@github.com

You're ready to push!

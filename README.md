# VideoConverter - Team 20

Members:

* Juan Manuel Jiménez - jm.jimenezc12@uniandes.edu.co
* Andrés Felipe Lombo – a.lombo@uniandes.edu.co
* Juan José Montenegro Pulido - jj.montenegro@uniandes.edu.co
* Camilo Andrés Romero Maldonado – ca.romerom1@uniandes.edu.co

## Postman API Documentation
[Postman API Documentation](https://documenter.getpostman.com/view/6679811/2s9YRCWB4j)

## Steps for executing the project

Copy the file `.env.example` and use `.env` as its name. If desired, the variables values can be changed.

> Change databases hosts & ports if needed to the desired GCPs VMs

Afterwards, from the repository root, run the following command:

``` sh
docker compose up --build <service_name>
```

> Note that `service_name` is required for specifying which service to run on which machine

> Ensure that `video_converter` and `api` services are run after all the other services

For running with GCP NFS server, mount the previosly set up server on the `video_converter` & `api` VMs on a newly created folder `storage` from the root of the repository

> Note: Ensure the server has a `media` folder with full permissions

To change the permissions of the `media` folder, run the following command

```bash
sudo chmod +777 media/
```

> Note: Ensure file server is set up correctly, you can follow this [post](https://www.digitalocean.com/community/tutorials/how-to-set-up-an-nfs-mount-on-debian-11)


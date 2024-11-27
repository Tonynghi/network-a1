# ASSIGNMENT 1: DEVELOP A NETWORK APPLICATION

## 1. Overview:

This project covers the assignment work about a torrent-like network application developed by Nghiem Pham Vy Nghi (Tonynghi) and Doan Viet Tien Dat (dvtdat)

## 2. User manual:

### 2.0. Cloning project

If this project is not on your local repository yet, do as follow. Navigate with the CLI to desired directory for the clone and simply enter these commands:

```bash
git clone https://github.com/Tonynghi/network-a1.git
```

In this section, we shall guide you through the process of downloading file and some relevant commands.

A small note before we start the manual is that each OS may have their own way to compile a file, in the writer's case, is the _"py"_ keywork. But if it is not the same for you, try other options like

```bash
python3 [Filename.py] [args]
```

or

```bash
python [Filename.py] [args]
```

### 2.1. Initialization

Open the CLI at the root directory where the file **tracker.py** resides and enter the following command to start the tracker app:

```bash
    py tracker.py
```

After that, the CLI should show something like this that indicates the server has been started on the default ip **localhost** and port number **7000**

At this part, let's leave the tracker for now and move on to the initialization of the peer apps. In the default repository, we have already provided you with 3 different folders named **peer1**, **peer2**, **peer3**, each contain a **data** folder which store the owned files of each peer and a file named **peer.py** that hold the source code of the peer app. For this test run, we will use all of them to better demonstrate the multi-file download aspect.

For each peer app, change directory inside the folder of each peer and then compile the **peer.py** file with arguments. The structure is:

```bash
    cd peer folder
    py peer.py peer id peer ip peer listen/upload port
```

For example:
**Peer 1**:

```bash
    cd peer1
    py peer.py peer1 localhost 7001
```

**Peer 2**:

```bash
    cd peer2
    py peer.py peer2 localhost 7002
```

**Peer 3**:

```bash
    cd peer3
    py peer.py peer3 localhost 7003
```

After that, the CLI should announce the initialization of the peer apps:

Not that the new line has a _>_ sign, this indicates that we have enter the CLI thread, and now we must use specific commands to interact with the app.

For now, no file has been seeded to the tracker, so let's start seeding some. To do that, in the CLI of each peer, we can enter the following command:

```bash
    SEED file name
```

Let's do that for **peer 1** and **peer 2**. Each of them has both files named **test1.txt** and **test2.txt** file in the data folder.

With peer 1, let's seed one file at a time:

```bash
    SEED test1.txt
```

Here we can see that the request from peer 1 has been logged onto the CLI, indicating that the tracker can receive **HTTP request**, in the case here is a **POST request**, from peer 1. Let's move forward with the seeding so that both peer 1 and peer 2 have seeded all their files to the tracker.

**Peer 1**:

```bash
    SEED test2.txt
```

**Peer 2**:

```bash
    SEED test1.txt test2.txt
```

Note that here in the peer 2's CLI, we attempted to seed **2** files at the same time. The response from the tracker with the **status code 200** indicates that it can recognizes 2 files have been seeded.

### 2.2.View seeded files

Back to the tracker, we have a useful command to check the seeded files, let's give it a try:

```bash
    view files
```

And the list of seeded files will be shown on the CLI along with its information, including the **name**, the **infohash**, the **size in bytes**, the **peers** that hold on the file. Each of the peer also has their **id** and **address displayed**. In the final line of printed information, we are also able to see the **total number** of files that have been seeded.

### 2.3.Download file

Next we shall experience the core step of our application, the download command. With seeded files containing **test1.txt** and **test2.txt**, we shall choose another peer that does not have these 2 files, which is **peer 3**.

In peer 3 CLI, we will try the download for both of the 2 seeded files at the same time to see if it can live up to the task:

```bash
    DOWNLOAD test1.txt test2.txt
```

First, we can see **2** responses with status code 200 indicates that the tracker has acknowledged 2 requests, which were handled by 2 different threads, and send back the needed information.

Then, the peer app moved on to establish 2 connections to both peer 1 and peer 2. Note that since there are 2 files, each file was held by 2 peers so it established many requests **in parallel** and send them. At each **stage** of fetching chunks or assembling chunks, the application did us a favor of logging the information onto the screen.

On the other side, upon receiving requests, the application also logged out some information regarding the requests.

### 2.4.Validate

In this step, we will do the checking manually to see if the application has run correctly. To do that, we shall compare the content of the files held by the original peer and the newly created file at the requesting peer.

On the right side, we choose 2 files from peer 1 and peer 2, which are the source, and on the right side, those 2 are corresponding version of peer 3.

By comparing the content inside, which are identical to each other, we can safely assume that the application has worked correctly.

### 2.5.Exit

Last but not least, after using the application, we can terminate the program by the following command, used for both tracker and peer:

```bash
    exit
```

After that, the program will print an announcement saying that it is shutting down.

## 3. Documents:

If you want to study further into the project, please refer to the pdf file named **Computer_Network\_\_\_Assignment_1** inside this repository. That document should cover all of the aspects about our application, from approach to implementation.

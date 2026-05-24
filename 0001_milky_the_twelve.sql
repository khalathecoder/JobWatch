CREATE TABLE `certifications` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`name` varchar(255) NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `certifications_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `companies` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`name` varchar(255) NOT NULL,
	`atsType` varchar(50),
	`careersUrl` varchar(1024),
	`verified` boolean NOT NULL DEFAULT false,
	`hasLiveRoles` boolean NOT NULL DEFAULT false,
	`sampleRoles` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `companies_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `companySuggestions` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`name` varchar(255) NOT NULL,
	`atsType` varchar(50),
	`careersUrl` varchar(1024),
	`industry` varchar(100),
	`hasLiveRoles` boolean NOT NULL DEFAULT false,
	`sampleRoles` text,
	`verified` boolean NOT NULL DEFAULT false,
	`status` enum('pending','approved','rejected') NOT NULL DEFAULT 'pending',
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `companySuggestions_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `education` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`degree` varchar(255) NOT NULL,
	`school` varchar(255) NOT NULL,
	`graduationDate` varchar(10),
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `education_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `experience` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`jobTitle` varchar(255) NOT NULL,
	`company` varchar(255) NOT NULL,
	`startDate` varchar(10),
	`endDate` varchar(10),
	`resumeVersion` enum('A','B','both') NOT NULL DEFAULT 'both',
	`responsibilities` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `experience_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `jobQueue` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`title` varchar(255) NOT NULL,
	`company` varchar(255) NOT NULL,
	`location` varchar(255),
	`url` varchar(1024) NOT NULL,
	`description` text,
	`keywords` text,
	`score` decimal(5,2),
	`scoreReason` text,
	`status` enum('pending','approved','rejected') NOT NULL DEFAULT 'pending',
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `jobQueue_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `jobs` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`title` varchar(255) NOT NULL,
	`company` varchar(255) NOT NULL,
	`location` varchar(255),
	`url` varchar(1024) NOT NULL,
	`description` text,
	`status` enum('new','saved','applied','rejected','archived') NOT NULL DEFAULT 'new',
	`keywords` text,
	`score` decimal(5,2),
	`scoreReason` text,
	`postedOn` timestamp,
	`foundAt` timestamp NOT NULL DEFAULT (now()),
	`seen` boolean NOT NULL DEFAULT false,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `jobs_id` PRIMARY KEY(`id`),
	CONSTRAINT `jobs_url_unique` UNIQUE(`url`)
);
--> statement-breakpoint
CREATE TABLE `scanLogs` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`company` varchar(255),
	`jobsFound` int NOT NULL DEFAULT 0,
	`status` enum('running','completed','failed') NOT NULL DEFAULT 'running',
	`error` text,
	`startedAt` timestamp NOT NULL DEFAULT (now()),
	`completedAt` timestamp,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `scanLogs_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `skills` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`category` varchar(100) NOT NULL,
	`items` text,
	`resumeVersion` enum('A','B','both') NOT NULL DEFAULT 'both',
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `skills_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `userProfiles` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`fullName` varchar(255),
	`phone` varchar(20),
	`website` varchar(255),
	`addressStreet` varchar(255),
	`addressCity` varchar(100),
	`addressState` varchar(2),
	`addressZip` varchar(10),
	`linkedIn` varchar(255),
	`github` varchar(255),
	`prefUsername` varchar(100),
	`prefPasswordHint` varchar(255),
	`resumeA` text,
	`resumeB` text,
	`passionStatement` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `userProfiles_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `webSaves` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`title` varchar(255) NOT NULL,
	`company` varchar(255) NOT NULL,
	`location` varchar(255),
	`url` varchar(1024) NOT NULL,
	`status` enum('pending','applied','archived') NOT NULL DEFAULT 'pending',
	`savedAt` timestamp NOT NULL DEFAULT (now()),
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `webSaves_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE INDEX `idx_userId` ON `certifications` (`userId`);--> statement-breakpoint
CREATE INDEX `idx_userId_name` ON `companies` (`userId`,`name`);--> statement-breakpoint
CREATE INDEX `idx_userId_status` ON `companySuggestions` (`userId`,`status`);--> statement-breakpoint
CREATE INDEX `idx_userId` ON `education` (`userId`);--> statement-breakpoint
CREATE INDEX `idx_userId` ON `experience` (`userId`);--> statement-breakpoint
CREATE INDEX `idx_userId_status` ON `jobQueue` (`userId`,`status`);--> statement-breakpoint
CREATE INDEX `idx_userId_status` ON `jobs` (`userId`,`status`);--> statement-breakpoint
CREATE INDEX `idx_company` ON `jobs` (`company`);--> statement-breakpoint
CREATE INDEX `idx_userId_company` ON `scanLogs` (`userId`,`company`);--> statement-breakpoint
CREATE INDEX `idx_userId` ON `skills` (`userId`);--> statement-breakpoint
CREATE INDEX `idx_userId_status` ON `webSaves` (`userId`,`status`);